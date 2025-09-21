import json
import os

class UserManager:
    """
    Manages user accounts and session data stored in a JSON file.

    Attributes:
        filename (str): Path to the JSON file storing user data.
        users (dict): Dictionary holding all user accounts and their session history.
    """

    def __init__(self, filename="users.json"):
        """
        Initialise the UserManager with a given filename.

        Args:
            filename (str, optional): Name of the JSON file for storing users. Defaults to "users.json".
        """
        self.filename = filename
        self.load_users()
    
    def load_users(self):
        """
        Load user data from the JSON file.

        If the file does not exist or cannot be read, an empty dictionary is used.
        """
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.users = json.load(f)
            except:
                self.users = {}
        else:
            self.users = {}
    
    def save_users(self):
        """
        Save all user data to the JSON file.

        Data is written in a human-readable format with indentation.
        """
        with open(self.filename, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def signup(self, username, password):
        """
        Create a new user account.

        Args:
            username (str): Desired username.
            password (str): Password for the account.

        Returns:
            tuple: (bool, str) where bool indicates success, 
                   and str provides a status message.
        """
        if username in self.users:
            return False, "Username already exists"
        self.users[username] = {
            "password": password, 
            "history": [],
            "total_sessions": 0,
            "total_duration_minutes": 0,
            "first_session": None
        }
        self.save_users()
        return True, "Account created successfully"
    
    def login(self, username, password):
        """
        Authenticate an existing user.

        Args:
            username (str): Username to log in.
            password (str): Password associated with the account.

        Returns:
            tuple: (bool, str) where bool indicates success,
                   and str provides a status message.
        """
        if username not in self.users:
            return False, "Username not found"
        if self.users[username]["password"] != password:
            return False, "Invalid password"
        return True, "Login successful"
    
    def save_session(self, username, session_data):
        """
        Save a single session entry for a given user.

        Args:
            username (str): Username to associate with the session.
            session_data (dict): Dictionary containing session details.
                Expected keys include:
                    - "start" (str): Timestamp when session started.
                    - "duration_minutes" (int): Duration of the session in minutes.

        Notes:
            - Updates total session count.
            - Updates total session duration.
            - Records the first session timestamp if not already set.
        """
        if username in self.users:
            user = self.users[username]
            user["history"].append(session_data)
            user["total_sessions"] += 1
            user["total_duration_minutes"] += session_data.get("duration_minutes", 0)
            
            if user["first_session"] is None:
                user["first_session"] = session_data["start"]
            
            self.save_users()
