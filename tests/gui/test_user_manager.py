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


def test_save_session_updates_stats(tmp_path):
    fn = str(tmp_path / 'u2.json')
    um = UserManager(filename=fn)
    um.signup('u', 'p')
    um.save_session('u', {'start': '2025-01-01T10:00:00', 'duration_minutes': 10})
    user = um.users['u']
    assert user['total_sessions'] == 1
    assert user['total_duration_minutes'] == 10