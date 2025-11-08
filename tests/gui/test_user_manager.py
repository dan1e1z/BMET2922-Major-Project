"""
Test module for UserManager.

Author: Daniel Lindsay-Shad
Note: The Docstrings for methods were generated using Generative AI based on the method functionality.
"""

import pytest
from gui.core.user_manager import UserManager


def test_signup_login_and_persistence(tmp_path):
    fn = str(tmp_path / 'u.json')
    um = UserManager(filename=fn)
    ok, msg = um.signup('u1', 'p')
    assert ok
    ok, msg = um.login('u1', 'p')
    assert ok

    # ensure file persisted
    um2 = UserManager(filename=fn)
    assert 'u1' in um2.users


def test_signup_existing_user(tmp_path):
    fn = str(tmp_path / 'dup.json')
    um = UserManager(filename=fn)
    assert um.signup('u1', 'p')[0]
    ok, msg = um.signup('u1', 'p')
    assert not ok
    assert msg == 'Username already exists'


def test_login_failures(tmp_path):
    fn = str(tmp_path / 'login.json')
    um = UserManager(filename=fn)
    um.signup('user', 'pass')

    ok, msg = um.login('missing', 'pass')
    assert not ok and msg == 'Username not found'

    ok, msg = um.login('user', 'wrong')
    assert not ok and msg == 'Invalid password'


def test_save_session_updates_stats(tmp_path):
    fn = str(tmp_path / 'u2.json')
    um = UserManager(filename=fn)
    um.signup('u', 'p')
    um.save_session('u', {'start': '2025-01-01T10:00:00', 'duration_minutes': 10})
    user = um.users['u']
    assert user['total_sessions'] == 1
    assert user['total_duration_minutes'] == 10
    assert user['first_session'] == '2025-01-01T10:00:00'


def test_save_session_ignores_unknown_user(tmp_path):
    fn = str(tmp_path / 'unknown.json')
    um = UserManager(filename=fn)
    # Should not raise
    um.save_session('ghost', {'start': '2025-01-01T10:00:00', 'duration_minutes': 5})


def test_load_invalid_json(tmp_path):
    fn = tmp_path / 'bad.json'
    fn.write_text('{ invalid json', encoding='utf-8')
    um = UserManager(filename=str(fn))
    assert um.users == {}