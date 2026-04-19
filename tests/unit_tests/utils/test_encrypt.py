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
from superset.utils.encrypt import _resolve_encryption_key


def test_resolve_encryption_key_prefers_dedicated_key() -> None:
    """
    ``DATABASE_ENCRYPTED_FIELD_KEY`` should take precedence over ``SECRET_KEY``
    so that a leak of ``SECRET_KEY`` does not compromise stored credentials.
    """
    app_config = {
        "SECRET_KEY": "app-secret",
        "DATABASE_ENCRYPTED_FIELD_KEY": "dedicated-db-key",
    }
    assert _resolve_encryption_key(app_config) == "dedicated-db-key"


def test_resolve_encryption_key_falls_back_to_secret_key_when_unset() -> None:
    """
    When no dedicated key is configured, fall back to ``SECRET_KEY`` to
    preserve backwards compatibility with existing deployments.
    """
    assert _resolve_encryption_key({"SECRET_KEY": "app-secret"}) == "app-secret"


def test_resolve_encryption_key_falls_back_when_dedicated_key_is_none() -> None:
    app_config = {"SECRET_KEY": "app-secret", "DATABASE_ENCRYPTED_FIELD_KEY": None}
    assert _resolve_encryption_key(app_config) == "app-secret"


def test_resolve_encryption_key_falls_back_when_dedicated_key_is_empty() -> None:
    app_config = {"SECRET_KEY": "app-secret", "DATABASE_ENCRYPTED_FIELD_KEY": ""}
    assert _resolve_encryption_key(app_config) == "app-secret"
