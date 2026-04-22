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

from unittest.mock import patch

from flask import current_app

from superset.views.base import get_error_msg

HIDDEN_MSG = (
    "FATAL ERROR \nStacktrace is hidden. Change the SHOW_STACKTRACE "
    "configuration setting to enable it"
)


def _trigger() -> str:
    try:
        raise RuntimeError("leak me")
    except RuntimeError:
        return get_error_msg()


def test_get_error_msg_hidden_when_config_disabled_even_for_admin():
    current_app.config["SHOW_STACKTRACE"] = False
    with patch("superset.views.base._current_user_is_admin", return_value=True):
        msg = _trigger()
    assert msg == HIDDEN_MSG


def test_get_error_msg_hidden_for_non_admin_when_config_enabled():
    current_app.config["SHOW_STACKTRACE"] = True
    with patch("superset.views.base._current_user_is_admin", return_value=False):
        msg = _trigger()
    assert msg == HIDDEN_MSG
    assert "leak me" not in msg
    assert "Traceback" not in msg


def test_get_error_msg_traceback_visible_for_admin_when_enabled():
    current_app.config["SHOW_STACKTRACE"] = True
    with patch("superset.views.base._current_user_is_admin", return_value=True):
        msg = _trigger()
    assert "Traceback" in msg
    assert "leak me" in msg


def test_current_user_is_admin_swallows_errors():
    """
    The helper must never raise — the error-handling path calls it and a
    secondary exception would mask the original error and could expose
    details in a different way.
    """
    from superset.views.base import _current_user_is_admin

    with patch("superset.views.base.security_manager") as mock_sm:
        # Configure is_admin to raise; helper must catch and return False.
        mock_sm.is_admin = lambda: (_ for _ in ()).throw(RuntimeError("no request ctx"))
        assert _current_user_is_admin() is False
