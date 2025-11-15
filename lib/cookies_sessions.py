"""Cookie and session management utilities"""

import time
import uuid
from typing import Dict, Optional


class Cookie:
    """Cookie management utilities"""
    
    @staticmethod
    def set_cookie(name: str, value: str, max_age: int = None, path: str = "/", 
                   http_only: bool = True, secure: bool = False, same_site: str = "Lax"):
        """Generate Set-Cookie header"""
        cookie_str = f"{name}={value}; Path={path}"
        if max_age:
            cookie_str += f"; Max-Age={max_age}"
        if http_only:
            cookie_str += "; HttpOnly"
        if secure:
            cookie_str += "; Secure"
        if same_site:
            cookie_str += f"; SameSite={same_site}"
        return cookie_str
    
    @staticmethod
    def parse_cookies(cookie_header: str) -> Dict[str, str]:
        """Parse Cookie header into dictionary"""
        cookies = {}
        if cookie_header:
            for item in cookie_header.split(';'):
                item = item.strip()
                if '=' in item:
                    name, value = item.split('=', 1)
                    cookies[name] = value
        return cookies
    
    @staticmethod
    def delete_cookie(name: str, path: str = "/"):
        """Generate Set-Cookie header to delete a cookie"""
        return f"{name}=; Path={path}; Max-Age=0"


class Session:
    """Simple in-memory session management"""
    _sessions = {}
    
    @classmethod
    def create(cls, data: Dict = None, max_age: int = 3600) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        cls._sessions[session_id] = {
            'data': data or {},
            'created_at': time.time(),
            'max_age': max_age
        }
        return session_id
    
    @classmethod
    def get(cls, session_id: str) -> Optional[Dict]:
        """Get session data"""
        session = cls._sessions.get(session_id)
        if session:
            # Check if expired
            if time.time() - session['created_at'] > session['max_age']:
                cls.destroy(session_id)
                return None
            return session['data']
        return None
    
    @classmethod
    def update(cls, session_id: str, data: Dict):
        """Update session data"""
        if session_id in cls._sessions:
            cls._sessions[session_id]['data'].update(data)
    
    @classmethod
    def destroy(cls, session_id: str):
        """Destroy a session"""
        cls._sessions.pop(session_id, None)
