"""Middleware system for request/response processing"""

import time
from typing import Callable, List
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse, unquote
import json

from .cookies_sessions import Cookie, Session


class Request:
    """Request object with parsed data"""
    def __init__(self, handler: BaseHTTPRequestHandler, body: bytes = b''):
        self.handler = handler
        self.method = handler.command
        self.path = handler.path
        self.headers = handler.headers
        self.body = body
        
        # Parse URL
        parsed = urlparse(self.path)
        self.url_path = parsed.path
        self.query_params = {k: v[0] if len(v) == 1 else v 
                            for k, v in parse_qs(parsed.query).items()}
        
        # Parse JSON body
        self.json_data = {}
        if body:
            try:
                self.json_data = json.loads(body)
            except:
                pass
        
        # Parse cookies
        cookie_header = handler.headers.get('Cookie', '')
        self.cookies = Cookie.parse_cookies(cookie_header)
        
        # Session
        self.session_id = self.cookies.get('session_id')
        self.session = Session.get(self.session_id) if self.session_id else None


class Response:
    """Response object for building responses"""
    def __init__(self):
        self.status_code = 200
        self.headers = {'Content-Type': 'application/json'}
        self.body = {}
        self.cookies_to_set = []
    
    def set_status(self, code: int):
        self.status_code = code
        return self
    
    def set_header(self, name: str, value: str):
        self.headers[name] = value
        return self
    
    def set_cookie(self, name: str, value: str, **kwargs):
        cookie_str = Cookie.set_cookie(name, value, **kwargs)
        self.cookies_to_set.append(cookie_str)
        return self
    
    def delete_cookie(self, name: str, path: str = "/"):
        cookie_str = Cookie.delete_cookie(name, path)
        self.cookies_to_set.append(cookie_str)
        return self
    
    def json(self, data):
        self.body = data
        return self
    
    def send(self, handler: BaseHTTPRequestHandler):
        """Send the response"""
        handler.send_response(self.status_code)
        for name, value in self.headers.items():
            handler.send_header(name, value)
        for cookie in self.cookies_to_set:
            handler.send_header('Set-Cookie', cookie)
        handler.end_headers()
        
        if isinstance(self.body, (dict, list)):
            handler.wfile.write(json.dumps(self.body).encode())
        else:
            handler.wfile.write(str(self.body).encode())


class Middleware:
    """Base middleware class"""
    def process_request(self, request: Request, response: Response) -> bool:
        """Process request. Return False to stop chain."""
        return True
    
    def process_response(self, request: Request, response: Response):
        """Process response after handler"""
        pass


class CORSMiddleware(Middleware):
    """CORS handling middleware"""
    def __init__(self, allowed_origins='*', allowed_methods='GET, POST, PUT, DELETE, OPTIONS',
                 allowed_headers='Content-Type, Authorization'):
        self.allowed_origins = allowed_origins
        self.allowed_methods = allowed_methods
        self.allowed_headers = allowed_headers
    
    def process_request(self, request: Request, response: Response) -> bool:
        response.set_header('Access-Control-Allow-Origin', self.allowed_origins)
        response.set_header('Access-Control-Allow-Methods', self.allowed_methods)
        response.set_header('Access-Control-Allow-Headers', self.allowed_headers)
        
        if request.method == 'OPTIONS':
            response.set_status(204)
            return False
        return True


class LoggingMiddleware(Middleware):
    """Request logging middleware"""
    def process_request(self, request: Request, response: Response) -> bool:
        request._start_time = time.time()
        return True
    
    def process_response(self, request: Request, response: Response):
        duration = time.time() - getattr(request, '_start_time', time.time())
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
              f"{request.method} {request.url_path} - {response.status_code} - {duration:.3f}s")


class AuthMiddleware(Middleware):
    """Authentication middleware"""
    def __init__(self, protected_routes: List[str] = None, auth_checker: Callable = None):
        self.protected_routes = protected_routes or []
        self.auth_checker = auth_checker or self._default_auth_checker
    
    def _default_auth_checker(self, request: Request) -> bool:
        """Default: check for session"""
        return request.session is not None
    
    def process_request(self, request: Request, response: Response) -> bool:
        # Check if route is protected
        for route in self.protected_routes:
            if request.url_path.startswith(route):
                if not self.auth_checker(request):
                    response.set_status(401)
                    from .responses import JSONResponse
                    response.json(JSONResponse.error("Unauthorized", 401))
                    return False
        return True
