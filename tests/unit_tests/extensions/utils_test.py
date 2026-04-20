# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Tests for extension bundle signature verification."""

from __future__ import annotations

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from flask import Flask

from superset.extensions.utils import (
    _compute_bundle_digest,
    ExtensionSignatureError,
    SIGNATURE_FILENAME,
    verify_bundle_signature,
)


def _generate_keypair() -> tuple[ed25519.Ed25519PrivateKey, str]:
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_pem = (
        private_key.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("utf-8")
    )
    return private_key, public_pem


def _sign_bundle(
    private_key: ed25519.Ed25519PrivateKey, file_dict: dict[str, bytes]
) -> dict[str, bytes]:
    signed = dict(file_dict)
    signed[SIGNATURE_FILENAME] = private_key.sign(_compute_bundle_digest(file_dict))
    return signed


def _app(**config: object) -> Flask:
    app = Flask(__name__)
    app.config.update(config)
    return app


def test_verify_bundle_signature_accepts_valid_signature() -> None:
    private_key, public_pem = _generate_keypair()
    bundle = {
        "manifest.json": b'{"id":"ext"}',
        "backend/src/mod.py": b"VALUE = 1\n",
    }
    signed = _sign_bundle(private_key, bundle)
    app = _app(EXTENSIONS_TRUSTED_PUBLIC_KEYS=[public_pem])
    with app.app_context():
        verify_bundle_signature(signed)


def test_verify_bundle_signature_rejects_tampered_payload() -> None:
    private_key, public_pem = _generate_keypair()
    bundle = {
        "manifest.json": b'{"id":"ext"}',
        "backend/src/mod.py": b"VALUE = 1\n",
    }
    signed = _sign_bundle(private_key, bundle)
    # Tamper with a file after signing.
    signed["backend/src/mod.py"] = b"VALUE = 2\n"
    app = _app(EXTENSIONS_TRUSTED_PUBLIC_KEYS=[public_pem])
    with app.app_context(), pytest.raises(ExtensionSignatureError):
        verify_bundle_signature(signed)


def test_verify_bundle_signature_rejects_unknown_signer() -> None:
    signer_private, _ = _generate_keypair()
    _, trusted_pem = _generate_keypair()
    bundle = {"manifest.json": b"{}", "backend/src/m.py": b"x = 1"}
    signed = _sign_bundle(signer_private, bundle)
    app = _app(EXTENSIONS_TRUSTED_PUBLIC_KEYS=[trusted_pem])
    with app.app_context(), pytest.raises(ExtensionSignatureError):
        verify_bundle_signature(signed)


def test_verify_bundle_signature_requires_signature_file_by_default() -> None:
    _, public_pem = _generate_keypair()
    bundle = {"manifest.json": b"{}", "backend/src/m.py": b"x = 1"}
    app = _app(EXTENSIONS_TRUSTED_PUBLIC_KEYS=[public_pem])
    with app.app_context(), pytest.raises(ExtensionSignatureError):
        verify_bundle_signature(bundle)


def test_verify_bundle_signature_allows_unsigned_when_flag_set() -> None:
    bundle = {"manifest.json": b"{}", "backend/src/m.py": b"x = 1"}
    app = _app(EXTENSIONS_ALLOW_UNSIGNED=True)
    with app.app_context():
        verify_bundle_signature(bundle)


def test_verify_bundle_signature_without_trusted_keys_is_error() -> None:
    private_key, _ = _generate_keypair()
    bundle = {"manifest.json": b"{}", "backend/src/m.py": b"x = 1"}
    signed = _sign_bundle(private_key, bundle)
    app = _app(EXTENSIONS_TRUSTED_PUBLIC_KEYS=[])
    with app.app_context(), pytest.raises(ExtensionSignatureError):
        verify_bundle_signature(signed)
