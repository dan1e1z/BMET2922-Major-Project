import pytest
import json
import os
from unittest.mock import mock_open

from gui.core.user_manager import UserManager


@pytest.fixture
def temp_users_file(tmp_path):
    """Create a temporary users file for testing."""
    return tmp_path / "test_users.json"


@pytest.fixture
def user_manager(temp_users_file):
    """Create a UserManager instance with a temporary file."""
    return UserManager(filename=str(temp_users_file))


@pytest.fixture
def populated_user_manager(temp_users_file):
    """Create a UserManager with pre-populated users."""
    manager = UserManager(filename=str(temp_users_file))
    manager.signup("testuser", "password123", "personal")
    manager.signup("advanceduser", "pass456", "advanced")
    return manager


class TestUserManagerInit:
    """Test UserManager initialization."""
    
    def test_init_creates_empty_users_dict_when_file_not_exists(self, temp_users_file):
        manager = UserManager(filename=str(temp_users_file))
        assert manager.users == {}
        assert manager.filename == str(temp_users_file)
    
    def test_init_loads_existing_users_file(self, temp_users_file):
        # Create a users file
        test_data = {
            "user1": {
                "password": "pass1",
                "account_type": "personal",
                "history": [],
                "total_sessions": 0,
                "total_duration_minutes": 0,
                "first_session": None
            }
        }
        with open(temp_users_file, 'w') as f:
            json.dump(test_data, f)
        
        manager = UserManager(filename=str(temp_users_file))
        assert "user1" in manager.users
        assert manager.users["user1"]["password"] == "pass1"
    
    def test_init_handles_corrupt_json_file(self, temp_users_file):
        # Create corrupted file
        with open(temp_users_file, 'w') as f:
            f.write("not valid json {")
        
        manager = UserManager(filename=str(temp_users_file))
        assert manager.users == {}


class TestLoadUsers:
    """Test load_users method."""
    
    def test_load_users_empty_file(self, temp_users_file):
        manager = UserManager(filename=str(temp_users_file))
        manager.load_users()
        assert manager.users == {}
    
    def test_load_users_valid_file(self, temp_users_file):
        test_data = {"user1": {"password": "pass1"}}
        with open(temp_users_file, 'w') as f:
            json.dump(test_data, f)
        
        manager = UserManager(filename=str(temp_users_file))
        manager.load_users()
        assert manager.users == test_data
    
    def test_load_users_handles_exception(self, user_manager, mocker):
        m = mocker.patch('builtins.open', mock_open())
        m.side_effect = Exception("Read error")
        user_manager.load_users()
        assert user_manager.users == {}


class TestSaveUsers:
    """Test save_users method."""
    
    def test_save_users_creates_file(self, temp_users_file):
        manager = UserManager(filename=str(temp_users_file))
        manager.users = {"user1": {"password": "pass1"}}
        manager.save_users()
        
        assert os.path.exists(temp_users_file)
        with open(temp_users_file, 'r') as f:
            data = json.load(f)
        assert data == manager.users
    
    def test_save_users_format(self, temp_users_file):
        manager = UserManager(filename=str(temp_users_file))
        manager.users = {"user1": {"password": "pass1"}}
        manager.save_users()
        
        with open(temp_users_file, 'r') as f:
            content = f.read()
        # Check for indentation (human-readable format)
        assert '\n' in content
        assert '  ' in content


class TestSignup:
    """Test signup method."""
    
    def test_signup_creates_new_user_personal(self, user_manager):
        success, message = user_manager.signup("newuser", "password123", "personal")
        
        assert success is True
        assert message == "Account created successfully"
        assert "newuser" in user_manager.users
        assert user_manager.users["newuser"]["password"] == "password123"
        assert user_manager.users["newuser"]["account_type"] == "personal"
    
    def test_signup_creates_new_user_advanced(self, user_manager):
        success, message = user_manager.signup("advuser", "pass456", "advanced")
        
        assert success is True
        assert user_manager.users["advuser"]["account_type"] == "advanced"
    
    def test_signup_initializes_user_fields(self, user_manager):
        user_manager.signup("newuser", "pass", "personal")
        user = user_manager.users["newuser"]
        
        assert user["history"] == []
        assert user["total_sessions"] == 0
        assert user["total_duration_minutes"] == 0
        assert user["first_session"] is None
    
    def test_signup_duplicate_username(self, user_manager):
        user_manager.signup("duplicate", "pass1", "personal")
        success, message = user_manager.signup("duplicate", "pass2", "personal")
        
        assert success is False
        assert message == "Username already exists"
        # Original password should remain
        assert user_manager.users["duplicate"]["password"] == "pass1"
    
    def test_signup_saves_to_file(self, temp_users_file):
        manager = UserManager(filename=str(temp_users_file))
        manager.signup("fileuser", "password", "personal")
        
        # Verify file was created
        assert os.path.exists(temp_users_file)
        
        # Load fresh manager to verify persistence
        new_manager = UserManager(filename=str(temp_users_file))
        assert "fileuser" in new_manager.users
    
    def test_signup_default_account_type(self, user_manager):
        success, _ = user_manager.signup("defaultuser", "pass")
        
        assert success is True
        assert user_manager.users["defaultuser"]["account_type"] == "personal"


class TestLogin:
    """Test login method."""
    
    def test_login_successful(self, populated_user_manager):
        success, message = populated_user_manager.login("testuser", "password123")
        
        assert success is True
        assert message == "Login successful"
    
    def test_login_user_not_found(self, populated_user_manager):
        success, message = populated_user_manager.login("nonexistent", "password")
        
        assert success is False
        assert message == "Username not found"
    
    def test_login_invalid_password(self, populated_user_manager):
        success, message = populated_user_manager.login("testuser", "wrongpassword")
        
        assert success is False
        assert message == "Invalid password"
    
    def test_login_case_sensitive_username(self, populated_user_manager):
        success, message = populated_user_manager.login("TestUser", "password123")
        
        assert success is False
        assert message == "Username not found"
    
    def test_login_case_sensitive_password(self, populated_user_manager):
        success, message = populated_user_manager.login("testuser", "Password123")
        
        assert success is False
        assert message == "Invalid password"


class TestSaveSession:
    """Test save_session method."""
    
    def test_save_session_adds_to_history(self, populated_user_manager):
        session_data = {
            "start": "2025-01-01T10:00:00",
            "duration_minutes": 10,
            "avg_bpm": 75.0
        }
        
        populated_user_manager.save_session("testuser", session_data)
        
        user = populated_user_manager.users["testuser"]
        assert len(user["history"]) == 1
        assert user["history"][0] == session_data
    
    def test_save_session_increments_total_sessions(self, populated_user_manager):
        session_data = {
            "start": "2025-01-01T10:00:00",
            "duration_minutes": 10
        }
        
        initial_count = populated_user_manager.users["testuser"]["total_sessions"]
        populated_user_manager.save_session("testuser", session_data)
        
        assert populated_user_manager.users["testuser"]["total_sessions"] == initial_count + 1
    
    def test_save_session_accumulates_duration(self, populated_user_manager):
        session1 = {"start": "2025-01-01T10:00:00", "duration_minutes": 10}
        session2 = {"start": "2025-01-01T11:00:00", "duration_minutes": 15}
        
        populated_user_manager.save_session("testuser", session1)
        populated_user_manager.save_session("testuser", session2)
        
        assert populated_user_manager.users["testuser"]["total_duration_minutes"] == 25
    
    def test_save_session_sets_first_session(self, populated_user_manager):
        session_data = {
            "start": "2025-01-01T10:00:00",
            "duration_minutes": 10
        }
        
        populated_user_manager.save_session("testuser", session_data)
        
        assert populated_user_manager.users["testuser"]["first_session"] == "2025-01-01T10:00:00"
    
    def test_save_session_preserves_first_session(self, populated_user_manager):
        session1 = {"start": "2025-01-01T10:00:00", "duration_minutes": 10}
        session2 = {"start": "2025-01-02T10:00:00", "duration_minutes": 10}
        
        populated_user_manager.save_session("testuser", session1)
        populated_user_manager.save_session("testuser", session2)
        
        assert populated_user_manager.users["testuser"]["first_session"] == "2025-01-01T10:00:00"
    
    def test_save_session_nonexistent_user(self, user_manager):
        session_data = {"start": "2025-01-01T10:00:00", "duration_minutes": 10}
        
        # Should not raise an error, just not save
        user_manager.save_session("nonexistent", session_data)
        assert "nonexistent" not in user_manager.users
    
    def test_save_session_persists_to_file(self, temp_users_file):
        manager = UserManager(filename=str(temp_users_file))
        manager.signup("testuser", "pass", "personal")
        session_data = {"start": "2025-01-01T10:00:00", "duration_minutes": 10}
        
        manager.save_session("testuser", session_data)
        
        # Load fresh manager
        new_manager = UserManager(filename=str(temp_users_file))
        assert len(new_manager.users["testuser"]["history"]) == 1
    
    def test_save_session_multiple_sessions(self, populated_user_manager):
        sessions = [
            {"start": f"2025-01-0{i}T10:00:00", "duration_minutes": 10}
            for i in range(1, 6)
        ]
        
        for session in sessions:
            populated_user_manager.save_session("testuser", session)
        
        user = populated_user_manager.users["testuser"]
        assert len(user["history"]) == 5
        assert user["total_sessions"] == 5
        assert user["total_duration_minutes"] == 50
    
    def test_save_session_handles_missing_duration(self, populated_user_manager):
        session_data = {"start": "2025-01-01T10:00:00"}
        
        initial_duration = populated_user_manager.users["testuser"]["total_duration_minutes"]
        populated_user_manager.save_session("testuser", session_data)
        
        # Should not add to duration if key missing
        assert populated_user_manager.users["testuser"]["total_duration_minutes"] == initial_duration


class TestIntegration:
    """Integration tests for complete workflows."""
    
    def test_complete_user_lifecycle(self, temp_users_file):
        manager = UserManager(filename=str(temp_users_file))
        
        # Signup
        success, _ = manager.signup("integration_user", "password", "personal")
        assert success is True
        
        # Login
        success, _ = manager.login("integration_user", "password")
        assert success is True
        
        # Save multiple sessions
        for i in range(3):
            session = {
                "start": f"2025-01-0{i+1}T10:00:00",
                "duration_minutes": 15,
                "avg_bpm": 70 + i
            }
            manager.save_session("integration_user", session)
        
        user = manager.users["integration_user"]
        assert len(user["history"]) == 3
        assert user["total_sessions"] == 3
        assert user["total_duration_minutes"] == 45
        
        # Verify persistence
        new_manager = UserManager(filename=str(temp_users_file))
        assert len(new_manager.users["integration_user"]["history"]) == 3
    
    def test_multiple_users_independent(self, user_manager):
        # Create multiple users
        user_manager.signup("user1", "pass1", "personal")
        user_manager.signup("user2", "pass2", "advanced")
        
        # Save sessions for each
        user_manager.save_session("user1", {"start": "2025-01-01T10:00:00", "duration_minutes": 10})
        user_manager.save_session("user2", {"start": "2025-01-01T11:00:00", "duration_minutes": 20})
        
        # Verify independence
        assert len(user_manager.users["user1"]["history"]) == 1
        assert len(user_manager.users["user2"]["history"]) == 1
        assert user_manager.users["user1"]["total_duration_minutes"] == 10
        assert user_manager.users["user2"]["total_duration_minutes"] == 20