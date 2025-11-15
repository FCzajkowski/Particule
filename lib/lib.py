from typing import Any, Callable, Dict, List, Union, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid
import os
import mimetypes
from pathlib import Path
from urllib.parse import parse_qs, urlparse, unquote
import re
import html
from functools import wraps
import time
from datetime import datetime, timedelta

# ============= RESPONSE HELPERS =============

class JSONResponse:
    """Helper for consistent JSON responses"""
    
    @staticmethod
    def success(data=None, message=None):
        """Return success response"""
        response = {"ok": True}
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
        return response
    
    @staticmethod
    def error(message: str, code: int = 400, details=None):
        """Return error response"""
        response = {"ok": False, "error": message, "code": code}
        if details:
            response["details"] = details
        return response

# ============= COOKIE & SESSION MANAGEMENT =============

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

# ============= MIDDLEWARE SYSTEM =============

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
                    response.json(JSONResponse.error("Unauthorized", 401))
                    return False
        return True

# ============= FILE UPLOAD HANDLER =============

class FileUpload:
    """Handle multipart file uploads"""
    
    @staticmethod
    def parse_multipart(body: bytes, content_type: str) -> Dict[str, Any]:
        """Parse multipart/form-data"""
        # Extract boundary
        boundary = None
        for part in content_type.split(';'):
            if 'boundary=' in part:
                boundary = part.split('boundary=')[1].strip()
                break
        
        if not boundary:
            return {}
        
        # Parse parts
        boundary_bytes = f'--{boundary}'.encode()
        parts = body.split(boundary_bytes)
        
        result = {}
        for part in parts:
            if not part or part == b'--\r\n' or part == b'--':
                continue
            
            # Split headers and content
            if b'\r\n\r\n' in part:
                headers_section, content = part.split(b'\r\n\r\n', 1)
                content = content.rstrip(b'\r\n')
                
                # Parse Content-Disposition
                headers_str = headers_section.decode('utf-8', errors='ignore')
                name = None
                filename = None
                
                for line in headers_str.split('\r\n'):
                    if 'Content-Disposition' in line:
                        for item in line.split(';'):
                            if 'name=' in item:
                                name = item.split('name=')[1].strip('"')
                            if 'filename=' in item:
                                filename = item.split('filename=')[1].strip('"')
                
                if name:
                    if filename:
                        result[name] = {
                            'filename': filename,
                            'content': content,
                            'size': len(content)
                        }
                    else:
                        result[name] = content.decode('utf-8', errors='ignore')
        
        return result

# ============= FETCH WRAPPER =============

def create_fetch_helpers():
    """Generate JavaScript fetch helpers"""
    return """
    <script>
    window.api = {
        async get(url, options = {}) {
            const response = await fetch(url, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json', ...options.headers },
                ...options
            });
            return await response.json();
        },
        
        async post(url, data, options = {}) {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', ...options.headers },
                body: JSON.stringify(data),
                ...options
            });
            return await response.json();
        },
        
        async put(url, data, options = {}) {
            const response = await fetch(url, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json', ...options.headers },
                body: JSON.stringify(data),
                ...options
            });
            return await response.json();
        },
        
        async delete(url, options = {}) {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json', ...options.headers },
                ...options
            });
            return await response.json();
        }
    };
    </script>
    """

# ============= STATE MANAGEMENT (Enhanced) =============

class State:
    """State management similar to React useState"""
    def __init__(self, initial_value):
        self._value = initial_value
        self._listeners = []
    
    def get(self):
        return self._value
    
    def set(self, new_value):
        self._value = new_value
        for listener in self._listeners:
            listener()
    
    def subscribe(self, listener):
        self._listeners.append(listener)

class Ref:
    """Mutable reference that doesn't trigger re-renders"""
    def __init__(self, initial_value=None):
        self.current = initial_value

class ComputedState:
    """Derived state that updates automatically when dependencies change"""
    def __init__(self, compute_fn: Callable, *dependencies: State):
        self.compute_fn = compute_fn
        self.dependencies = dependencies
        self._cached_value = None
        self._is_dirty = True
        
        for dep in dependencies:
            dep.subscribe(self._mark_dirty)
    
    def _mark_dirty(self):
        self._is_dirty = True
    
    def get(self):
        if self._is_dirty:
            self._cached_value = self.compute_fn()
            self._is_dirty = False
        return self._cached_value

class Store:
    """Global store for state management (Redux-like) with persistence"""
    def __init__(self, initial_state: Dict, persist_keys: List[str] = None):
        self._state = initial_state
        self._listeners = []
        self._reducers = {}
        self._persist_keys = persist_keys or []
        self._middleware = []
        self._logger_enabled = False
    
    def get_state(self):
        return self._state.copy()
    
    def subscribe(self, listener: Callable):
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)
    
    def dispatch(self, action: Dict):
        """Dispatch an action to update state"""
        prev_state = self._state.copy()
        action_type = action.get('type')
        
        # Log action
        if self._logger_enabled:
            print(f"[STORE] Action: {action_type}")
            print(f"[STORE] Payload: {action}")
        
        # Process middleware
        for mw in self._middleware:
            action = mw(self._state, action)
            if action is None:
                return
        
        if action_type in self._reducers:
            self._state = self._reducers[action_type](self._state, action)
            
            # Log state change
            if self._logger_enabled:
                print(f"[STORE] Prev State: {prev_state}")
                print(f"[STORE] Next State: {self._state}")
            
            # Persist if needed
            self._persist()
            
            for listener in self._listeners:
                listener()
    
    def add_reducer(self, action_type: str, reducer: Callable):
        """Register a reducer for an action type"""
        self._reducers[action_type] = reducer
    
    def add_middleware(self, middleware: Callable):
        """Add middleware (state, action) => action"""
        self._middleware.append(middleware)
    
    def enable_logger(self):
        """Enable action/state logging"""
        self._logger_enabled = True
    
    def _persist(self):
        """Persist specified keys to localStorage (client-side only)"""
        if self._persist_keys:
            persist_data = {k: self._state.get(k) for k in self._persist_keys if k in self._state}
            # This would be handled client-side with localStorage
            pass

# Global store instance
_global_store = None

def create_store(initial_state: Dict, persist_keys: List[str] = None) -> Store:
    """Create a global store"""
    global _global_store
    _global_store = Store(initial_state, persist_keys)
    return _global_store

def use_store() -> Store:
    """Get the global store"""
    return _global_store

# ============= COMPONENT LIFECYCLE (Enhanced) =============

class Context:
    """Context for sharing data across component tree"""
    def __init__(self, default_value=None):
        self._value = default_value
        self._consumers = []
    
    def provide(self, value):
        """Set context value"""
        self._value = value
        for consumer in self._consumers:
            consumer(value)
    
    def consume(self, callback):
        """Subscribe to context changes"""
        self._consumers.append(callback)
        callback(self._value)
        return lambda: self._consumers.remove(callback)
    
    def get_value(self):
        """Get current context value"""
        return self._value

def create_context(default_value=None):
    """Create a new context"""
    return Context(default_value)

class Component:
    """Base component class with lifecycle methods"""
    def __init__(self, **props):
        self.props = props
        self.state = {}
        self._is_mounted = False
        self._cleanup_handlers = []
        self._refs = {}
    
    def use_state(self, initial_value):
        """Hook for state management"""
        return State(initial_value)
    
    def use_ref(self, initial_value=None):
        """Hook for mutable ref"""
        return Ref(initial_value)
    
    def use_computed(self, compute_fn: Callable, *dependencies: State):
        """Hook for computed/derived state"""
        return ComputedState(compute_fn, *dependencies)
    
    def use_context(self, context: Context):
        """Hook for context consumption"""
        return context.get_value()
    
    def component_did_mount(self):
        """Called after component is rendered"""
        pass
    
    def component_will_unmount(self):
        """Called before component is removed"""
        pass
    
    def component_did_update(self, prev_props: Dict, prev_state: Dict):
        """Called after props or state change"""
        pass
    
    def _mount(self):
        """Internal mount lifecycle"""
        if not self._is_mounted:
            self._is_mounted = True
            self.component_did_mount()
    
    def _unmount(self):
        """Internal unmount lifecycle"""
        if self._is_mounted:
            self._is_mounted = False
            for cleanup in self._cleanup_handlers:
                cleanup()
            self.component_will_unmount()
    
    def render(self):
        """Must be implemented by child classes"""
        raise NotImplementedError("Component must implement render method")

# ============= ENHANCED EVENT HANDLING =============

class JSBuilder:
    """Builds JavaScript code from Python-like syntax"""
    
    @staticmethod
    def alert(message):
        return f"alert('{message}')"
    
    @staticmethod
    def console_log(*args):
        args_str = ', '.join(f"'{arg}'" if isinstance(arg, str) else str(arg) for arg in args)
        return f"console.log({args_str})"
    
    @staticmethod
    def set_text(element_id, text):
        return f"document.getElementById('{element_id}').textContent = '{text}'"
    
    @staticmethod
    def get_value(element_id):
        return f"document.getElementById('{element_id}').value"
    
    @staticmethod
    def toggle_class(element_id, class_name):
        return f"document.getElementById('{element_id}').classList.toggle('{class_name}')"
    
    @staticmethod
    def add_class(element_id, class_name):
        return f"document.getElementById('{element_id}').classList.add('{class_name}')"
    
    @staticmethod
    def remove_class(element_id, class_name):
        return f"document.getElementById('{element_id}').classList.remove('{class_name}')"
    
    @staticmethod
    def set_style(element_id, property_name, value):
        return f"document.getElementById('{element_id}').style.{property_name} = '{value}'"
    
    @staticmethod
    def navigate_to(path):
        """Navigate to a route"""
        return f"window.location.hash = '{path}'"

class PyScript:
    """Container for Python-like JavaScript code"""
    def __init__(self):
        self.statements = []
        self.js = JSBuilder()
    
    def alert(self, message):
        self.statements.append(self.js.alert(message))
        return self
    
    def log(self, *args):
        self.statements.append(self.js.console_log(*args))
        return self
    
    def set_text(self, element_id, text):
        self.statements.append(self.js.set_text(element_id, text))
        return self
    
    def toggle_class(self, element_id, class_name):
        self.statements.append(self.js.toggle_class(element_id, class_name))
        return self
    
    def add_class(self, element_id, class_name):
        self.statements.append(self.js.add_class(element_id, class_name))
        return self
    
    def remove_class(self, element_id, class_name):
        self.statements.append(self.js.remove_class(element_id, class_name))
        return self
    
    def set_style(self, element_id, property_name, value):
        self.statements.append(self.js.set_style(element_id, property_name, value))
        return self
    
    def navigate(self, path):
        """Navigate to a route"""
        self.statements.append(self.js.navigate_to(path))
        return self
    
    def prevent_default(self):
        """Prevent default event behavior"""
        self.statements.append("event.preventDefault()")
        return self
    
    def stop_propagation(self):
        """Stop event propagation"""
        self.statements.append("event.stopPropagation()")
        return self
    
    def increment_counter(self, element_id):
        js_code = f"""
        let el = document.getElementById('{element_id}');
        let currentValue = parseInt(el.textContent) || 0;
        el.textContent = currentValue + 1;
        """
        self.statements.append(js_code)
        return self
    
    def decrement_counter(self, element_id):
        js_code = f"""
        let el = document.getElementById('{element_id}');
        let currentValue = parseInt(el.textContent) || 0;
        el.textContent = currentValue - 1;
        """
        self.statements.append(js_code)
        return self
    
    def toggle_visibility(self, element_id):
        js_code = f"""
        let el = document.getElementById('{element_id}');
        el.style.display = el.style.display === 'none' ? 'block' : 'none';
        """
        self.statements.append(js_code)
        return self
    
    def append_item(self, list_id, item_text):
        """Append an item to a list"""
        js_code = f"""
        let list = document.getElementById('{list_id}');
        let li = document.createElement('li');
        li.textContent = {item_text};
        list.appendChild(li);
        """
        self.statements.append(js_code)
        return self
    
    def clear_input(self, input_id):
        self.statements.append(f"document.getElementById('{input_id}').value = ''")
        return self
    
    def get_value(self, input_id):
        """Get the value from an input - returns JS expression"""
        return f"document.getElementById('{input_id}').value"
    
    def custom(self, js_code):
        self.statements.append(js_code)
        return self
    
    def to_js(self):
        return '; '.join(self.statements) + ';'

# Event handler decorators
def on_click(script_func):
    script = PyScript()
    script_func(script)
    return script.to_js()

def on_click_prevent(script_func):
    """Click handler with preventDefault"""
    script = PyScript()
    script.prevent_default()
    script_func(script)
    return script.to_js()

def on_submit_prevent(script_func):
    """Submit handler with preventDefault"""
    script = PyScript()
    script.prevent_default()
    script_func(script)
    return script.to_js()

# ============= ANIMATIONS =============

class Animation:
    """JavaScript animation helpers"""
    
    @staticmethod
    def fade_in(element_id, duration_ms=300):
        return f"""
        (function() {{
            let el = document.getElementById('{element_id}');
            el.style.opacity = '0';
            el.style.display = 'block';
            let start = null;
            function animate(timestamp) {{
                if (!start) start = timestamp;
                let progress = (timestamp - start) / {duration_ms};
                el.style.opacity = Math.min(progress, 1);
                if (progress < 1) requestAnimationFrame(animate);
            }}
            requestAnimationFrame(animate);
        }})();
        """
    
    @staticmethod
    def fade_out(element_id, duration_ms=300):
        return f"""
        (function() {{
            let el = document.getElementById('{element_id}');
            let start = null;
            function animate(timestamp) {{
                if (!start) start = timestamp;
                let progress = (timestamp - start) / {duration_ms};
                el.style.opacity = 1 - Math.min(progress, 1);
                if (progress < 1) {{
                    requestAnimationFrame(animate);
                }} else {{
                    el.style.display = 'none';
                }}
            }}
            requestAnimationFrame(animate);
        }})();
        """
    
    @staticmethod
    def slide_down(element_id, duration_ms=300):
        return f"""
        (function() {{
            let el = document.getElementById('{element_id}');
            el.style.height = '0px';
            el.style.overflow = 'hidden';
            el.style.display = 'block';
            let targetHeight = el.scrollHeight;
            let start = null;
            function animate(timestamp) {{
                if (!start) start = timestamp;
                let progress = (timestamp - start) / {duration_ms};
                el.style.height = (targetHeight * Math.min(progress, 1)) + 'px';
                if (progress < 1) requestAnimationFrame(animate);
                else el.style.height = 'auto';
            }}
            requestAnimationFrame(animate);
        }})();
        """
    
    @staticmethod
    def chain(*animations):
        """Chain multiple animations"""
        return ''.join(animations)

# ============= ENHANCED ROUTING =============

class Router:
    """Enhanced SPA router with params, guards, and transitions"""
    def __init__(self):
        self.routes = {}
        self.not_found = None
        self.guards = {}
        self.transition_duration = 200
    
    def add_route(self, path: str, component: Callable, guard: Callable = None):
        """Register a route with optional guard"""
        self.routes[path] = component
        if guard:
            self.guards[path] = guard
    
    def set_not_found(self, component: Callable):
        """Set 404 component"""
        self.not_found = component
    
    def set_transition_duration(self, duration_ms: int):
        """Set route transition duration"""
        self.transition_duration = duration_ms
    
    def _match_route(self, path: str):
        """Match route with parameters"""
        # Exact match
        if path in self.routes:
            return path, {}
        
        # Try pattern matching
        for route_pattern in self.routes.keys():
            if ':' in route_pattern:
                pattern_parts = route_pattern.split('/')
                path_parts = path.split('/')
                
                if len(pattern_parts) == len(path_parts):
                    params = {}
                    match = True
                    
                    for pattern_part, path_part in zip(pattern_parts, path_parts):
                        if pattern_part.startswith(':'):
                            param_name = pattern_part[1:]
                            params[param_name] = unquote(path_part)
                        elif pattern_part != path_part:
                            match = False
                            break
                    
                    if match:
                        return route_pattern, params
        
        return None, {}
    
    def get_route_js(self):
        """Generate JavaScript router code with transitions"""
        routes_html = {}
        for path, component in self.routes.items():
            comp_instance = component()
            if isinstance(comp_instance, Component):
                rendered = comp_instance.render()
            else:
                rendered = comp_instance
            routes_html[path] = rendered.to_html() if isinstance(rendered, Element) else str(rendered)
        
        not_found_html = ""
        if self.not_found:
            nf_instance = self.not_found()
            if isinstance(nf_instance, Component):
                rendered = nf_instance.render()
            else:
                rendered = nf_instance
            not_found_html = rendered.to_html() if isinstance(rendered, Element) else str(rendered)
        
        routes_json = json.dumps(routes_html)
        not_found_json = json.dumps(not_found_html)
        
        return f"""
        <script>
        const routesMap = {routes_json};
        const notFoundHTML = {not_found_json};
        const transitionDuration = {self.transition_duration};
        
        function matchRoute(path) {{
            // Exact match
            if (routesMap[path]) return {{ route: path, params: {{}} }};
            
            // Pattern matching
            for (let pattern in routesMap) {{
                if (pattern.includes(':')) {{
                    const patternParts = pattern.split('/');
                    const pathParts = path.split('/');
                    
                    if (patternParts.length === pathParts.length) {{
                        const params = {{}};
                        let match = true;
                        
                        for (let i = 0; i < patternParts.length; i++) {{
                            if (patternParts[i].startsWith(':')) {{
                                const paramName = patternParts[i].substring(1);
                                params[paramName] = decodeURIComponent(pathParts[i]);
                            }} else if (patternParts[i] !== pathParts[i]) {{
                                match = false;
                                break;
                            }}
                        }}
                        
                        if (match) return {{ route: pattern, params }};
                    }}
                }}
            }}
            
            return {{ route: null, params: {{}} }};
        }}
        
        async function renderRoute() {{
            const hash = window.location.hash.slice(1) || '/';
            const app = document.getElementById('app');
            const {{ route, params }} = matchRoute(hash);
            
            // Store params globally for access
            window.routeParams = params;
            
            // Fade out
            app.style.opacity = '1';
            app.style.transition = `opacity ${{transitionDuration}}ms`;
            app.style.opacity = '0';
            
            await new Promise(resolve => setTimeout(resolve, transitionDuration));
            
            if (route && routesMap[route]) {{
                app.innerHTML = routesMap[route];
            }} else {{
                app.innerHTML = notFoundHTML || '<h1>404 - Page Not Found</h1>';
            }}
            
            // Fade in
            app.style.opacity = '1';
        }}
        
        window.addEventListener('hashchange', renderRoute);
        window.addEventListener('load', renderRoute);
        </script>
        """

# ============= VIRTUAL DOM (Enhanced) =============

class Element:
    """Represents a virtual DOM element with better escaping"""
    def __init__(self, tag: str, props: Dict = None, *children):
        self.tag = tag
        self.props = props or {}
        self.children = list(children) if children else []
        self.key = props.get('key') if props else None
    
    def _escape_html(self, text: str) -> str:
        """Safely escape HTML content"""
        return html.escape(str(text))
    
    def _escape_attribute(self, value: str) -> str:
        """Safely escape attribute values"""
        return html.escape(str(value), quote=True)
    
    def to_html(self) -> str:
        if self.tag == 'text':
            content = str(self.props.get('content', ''))
            return self._escape_html(content)
        
        # Handle event handlers
        props_copy = self.props.copy()
        for key in list(props_copy.keys()):
            if key.startswith('on_'):
                event_name = key[3:]
                handler_code = props_copy[key]
                
                if callable(handler_code):
                    script = PyScript()
                    handler_code(script)
                    handler_code = script.to_js()
                
                props_copy[f'on{event_name}'] = handler_code
                del props_copy[key]
        self.props = props_copy
        
        # Handle style dict
        if 'style' in self.props and isinstance(self.props['style'], dict):
            style_str = '; '.join(f"{k.replace('_', '-')}: {v}" for k, v in self.props['style'].items())
            self.props['style'] = style_str
        
        # Merge classes
        if 'class' in self.props and 'className' in self.props:
            self.props['class'] = f"{self.props['class']} {self.props['className']}"
            del self.props['className']
        
        # Build attributes
        attrs = []
        for key, value in self.props.items():
            if key in ['key', 'ref']:
                continue
            attr_name = key.replace('_', '-')
            if key == 'className':
                attr_name = 'class'
            
            # Escape attribute values
            escaped_value = self._escape_attribute(value)
            attrs.append(f'{attr_name}="{escaped_value}"')
        
        attrs_str = ' ' + ' '.join(attrs) if attrs else ''
        
        # Self-closing tags
        if self.tag in ['img', 'br', 'hr', 'input', 'meta', 'link']:
            return f'<{self.tag}{attrs_str} />'
        
        # Render children
        children_html = ''.join(
            child.to_html() if isinstance(child, Element) else self._escape_html(str(child))
            for child in self.children
        )
        
        return f'<{self.tag}{attrs_str}>{children_html}</{self.tag}>'

# ============= SVG ELEMENTS =============

def svg(props: Dict = None, *children) -> Element:
    """SVG container"""
    default_props = {'xmlns': 'http://www.w3.org/2000/svg'}
    merged_props = {**default_props, **(props or {})}
    return Element('svg', merged_props, *children)

def path(props: Dict = None) -> Element:
    """SVG path"""
    return Element('path', props)

def circle(props: Dict = None) -> Element:
    """SVG circle"""
    return Element('circle', props)

def rect(props: Dict = None) -> Element:
    """SVG rectangle"""
    return Element('rect', props)

def line(props: Dict = None) -> Element:
    """SVG line"""
    return Element('line', props)

def polygon(props: Dict = None) -> Element:
    """SVG polygon"""
    return Element('polygon', props)

def ellipse(props: Dict = None) -> Element:
    """SVG ellipse"""
    return Element('ellipse', props)

def g(props: Dict = None, *children) -> Element:
    """SVG group"""
    return Element('g', props, *children)

# ============= ELEMENT CREATION =============

def create_element(tag: str, props: Dict = None, *children) -> Element:
    return Element(tag, props, *children)

def text(content: str) -> Element:
    return Element('text', {'content': content})

def fragment(*children) -> Element:
    """React.Fragment equivalent"""
    return div(None, *children)

# HTML Elements
def div(props: Dict = None, *children) -> Element:
    return create_element('div', props, *children)

def h1(props: Dict = None, *children) -> Element:
    return create_element('h1', props, *children)

def h2(props: Dict = None, *children) -> Element:
    return create_element('h2', props, *children)

def h3(props: Dict = None, *children) -> Element:
    return create_element('h3', props, *children)

def h4(props: Dict = None, *children) -> Element:
    return create_element('h4', props, *children)

def h5(props: Dict = None, *children) -> Element:
    return create_element('h5', props, *children)

def h6(props: Dict = None, *children) -> Element:
    return create_element('h6', props, *children)

def p(props: Dict = None, *children) -> Element:
    return create_element('p', props, *children)

def button(props: Dict = None, *children) -> Element:
    return create_element('button', props, *children)

def input_field(props: Dict = None) -> Element:
    return create_element('input', props)

def textarea(props: Dict = None, *children) -> Element:
    return create_element('textarea', props, *children)

def select(props: Dict = None, *children) -> Element:
    return create_element('select', props, *children)

def option(props: Dict = None, *children) -> Element:
    return create_element('option', props, *children)

def label(props: Dict = None, *children) -> Element:
    return create_element('label', props, *children)

def form(props: Dict = None, *children) -> Element:
    return create_element('form', props, *children)

def span(props: Dict = None, *children) -> Element:
    return create_element('span', props, *children)

def ul(props: Dict = None, *children) -> Element:
    return create_element('ul', props, *children)

def ol(props: Dict = None, *children) -> Element:
    return create_element('ol', props, *children)

def li(props: Dict = None, *children) -> Element:
    return create_element('li', props, *children)

def img(props: Dict = None) -> Element:
    return create_element('img', props)

def a(props: Dict = None, *children) -> Element:
    return create_element('a', props, *children)

def br() -> Element:
    return create_element('br')

def hr() -> Element:
    return create_element('hr')

def section(props: Dict = None, *children) -> Element:
    return create_element('section', props, *children)

def article(props: Dict = None, *children) -> Element:
    return create_element('article', props, *children)

def header(props: Dict = None, *children) -> Element:
    return create_element('header', props, *children)

def footer(props: Dict = None, *children) -> Element:
    return create_element('footer', props, *children)

def nav(props: Dict = None, *children) -> Element:
    return create_element('nav', props, *children)

def main(props: Dict = None, *children) -> Element:
    return create_element('main', props, *children)

def aside(props: Dict = None, *children) -> Element:
    return create_element('aside', props, *children)

def table(props: Dict = None, *children) -> Element:
    return create_element('table', props, *children)

def thead(props: Dict = None, *children) -> Element:
    return create_element('thead', props, *children)

def tbody(props: Dict = None, *children) -> Element:
    return create_element('tbody', props, *children)

def tr(props: Dict = None, *children) -> Element:
    return create_element('tr', props, *children)

def th(props: Dict = None, *children) -> Element:
    return create_element('th', props, *children)

def td(props: Dict = None, *children) -> Element:
    return create_element('td', props, *children)

def code(props: Dict = None, *children) -> Element:
    return create_element('code', props, *children)

def pre(props: Dict = None, *children) -> Element:
    return create_element('pre', props, *children)

def strong(props: Dict = None, *children) -> Element:
    return create_element('strong', props, *children)

def em(props: Dict = None, *children) -> Element:
    return create_element('em', props, *children)

def blockquote(props: Dict = None, *children) -> Element:
    return create_element('blockquote', props, *children)

def canvas(props: Dict = None, *children) -> Element:
    return create_element('canvas', props, *children)

def video(props: Dict = None, *children) -> Element:
    return create_element('video', props, *children)

def audio(props: Dict = None, *children) -> Element:
    return create_element('audio', props, *children)

# ============= FORM VALIDATION =============

class FormValidator:
    """Form validation utilities"""
    
    @staticmethod
    def required(value):
        return bool(value and str(value).strip())
    
    @staticmethod
    def email(value):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return bool(re.match(pattern, str(value)))
    
    @staticmethod
    def min_length(value, length):
        return len(str(value)) >= length
    
    @staticmethod
    def max_length(value, length):
        return len(str(value)) <= length
    
    @staticmethod
    def pattern(value, regex_pattern):
        return bool(re.match(regex_pattern, str(value)))
    
    @staticmethod
    def phone(value):
        """Validate phone number"""
        pattern = r'^[\d\s\-\+\(\)]+'
        return bool(re.match(pattern, str(value)))
    
    @staticmethod
    def url(value):
        """Validate URL"""
        pattern = r'^https?://[^\s]+'
        return bool(re.match(pattern, str(value)))

def create_form_component(fields: List[Dict], on_submit: Callable):
    """Create a form component with automatic validation"""
    def FormComponent():
        field_elements = []
        for field in fields:
            field_id = field.get('id', field['name'])
            field_type = field.get('type', 'text')
            field_label = field.get('label', field['name'])
            required = field.get('required', False)
            
            field_elements.extend([
                label({'for': field_id}, text(field_label)),
                input_field({
                    'type': field_type,
                    'id': field_id,
                    'name': field['name'],
                    'required': 'required' if required else None
                }),
                br()
            ])
        
        return form(
            {'on_submit': on_submit_prevent(lambda s: (s.custom(on_submit), s))},
            *field_elements,
            button({'type': 'submit'}, text('Submit'))
        )
    
    return FormComponent

# ============= INPUT MASKING =============

def create_input_mask_js():
    """Generate JavaScript for input masking"""
    return """
    <script>
    window.inputMasks = {
        phone: function(input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length > 0) {
                    value = value.match(/(\d{0,3})(\d{0,3})(\d{0,4})/);
                    e.target.value = !value[2] ? value[1] : '(' + value[1] + ') ' + value[2] + (value[3] ? '-' + value[3] : '');
                }
            });
        },
        
        date: function(input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length > 0) {
                    value = value.match(/(\d{0,2})(\d{0,2})(\d{0,4})/);
                    e.target.value = value[1] + (value[2] ? '/' + value[2] : '') + (value[3] ? '/' + value[3] : '');
                }
            });
        },
        
        currency: function(input) {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/[^\d.]/g, '');
                let parts = value.split('.');
                parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ',');
                if (parts.length > 1) {
                    parts[1] = parts[1].substring(0, 2);
                }
                e.target.value = ' + parts.join('.');
            });
        }
    };
    </script>
    """

# ============= APP CLASS (Enhanced) =============

class App:
    """Main application class with enhanced server"""
    def __init__(self, root_component: Callable):
        self.root_component = root_component
        self.port = 6500
        self.static_dir = 'static'
        self.api_routes = {}
        self.router = None
        self.middlewares = []
        self.enable_cors = False
        self.enable_logging = False
        self.minify_html = False
    
    def add_api_route(self, path: str, method: str, handler: Callable):
        """Add an API route"""
        self.api_routes[(path, method)] = handler
    
    def add_middleware(self, middleware: Middleware):
        """Add middleware to the app"""
        self.middlewares.append(middleware)
    
    def use_cors(self, **kwargs):
        """Enable CORS"""
        self.enable_cors = True
        self.add_middleware(CORSMiddleware(**kwargs))
    
    def use_logging(self):
        """Enable request logging"""
        self.enable_logging = True
        self.add_middleware(LoggingMiddleware())
    
    def use_auth(self, protected_routes: List[str] = None, auth_checker: Callable = None):
        """Enable authentication middleware"""
        self.add_middleware(AuthMiddleware(protected_routes, auth_checker))
    
    def set_static_dir(self, directory: str):
        """Set static files directory"""
        self.static_dir = directory
    
    def use_router(self, router: Router):
        """Enable routing"""
        self.router = router
    
    def enable_minification(self):
        """Enable HTML minification"""
        self.minify_html = True
    
    def render_to_html(self) -> str:
        component_instance = self.root_component()
        if isinstance(component_instance, Component):
            rendered = component_instance.render()
        else:
            rendered = component_instance
        
        body_html = rendered.to_html() if isinstance(rendered, Element) else str(rendered)
        
        router_js = self.router.get_route_js() if self.router else ""
        fetch_helpers = create_fetch_helpers()
        input_masks = create_input_mask_js()
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Particle App</title>
    <link rel="icon" type="image/svg+xml" href="static/Logo.svg">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
                sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
    </style>
</head>
<body>
    <div id="app">{body_html}</div>
    {fetch_helpers}
    {input_masks}
    {router_js}
</body>
</html>"""
        
        if self.minify_html:
            # Simple minification
            html_content = re.sub(r'\s+', ' ', html_content)
            html_content = re.sub(r'>\s+<', '><', html_content)
        
        return html_content
    
    def run(self, port: int = None):
        """Start the development server"""
        if port:
            self.port = port
        
        app_instance = self
        
        class RequestHandler(BaseHTTPRequestHandler):
            def _process_middlewares(self, request: Request, response: Response) -> bool:
                """Process middleware chain"""
                for middleware in app_instance.middlewares:
                    if not middleware.process_request(request, response):
                        return False
                return True
            
            def _process_response_middlewares(self, request: Request, response: Response):
                """Process response middlewares"""
                for middleware in app_instance.middlewares:
                    middleware.process_response(request, response)
            
            def do_OPTIONS(self):
                """Handle OPTIONS requests for CORS"""
                response = Response()
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else b''
                request = Request(self, body)
                
                if self._process_middlewares(request, response):
                    response.set_status(204)
                
                response.send(self)
            
            def do_GET(self):
                parsed_path = urlparse(self.path)
                path = parsed_path.path
                
                response = Response()
                request = Request(self)
                
                # Process middlewares
                if not self._process_middlewares(request, response):
                    response.send(self)
                    return
                
                # Serve static files
                if path.startswith('/static/'):
                    self.serve_static_file(path[8:])
                # Serve API routes
                elif (path, 'GET') in app_instance.api_routes:
                    self.handle_api_request('GET', path, request, response)
                # Serve main app
                else:
                    response.set_header('Content-Type', 'text/html')
                    html = app_instance.render_to_html()
                    response.body = html
                    response.send(self)
            
            def do_POST(self):
                parsed_path = urlparse(self.path)
                path = parsed_path.path
                
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else b''
                
                response = Response()
                request = Request(self, body)
                
                # Process middlewares
                if not self._process_middlewares(request, response):
                    response.send(self)
                    return
                
                # Handle file uploads
                content_type = self.headers.get('Content-Type', '')
                if 'multipart/form-data' in content_type:
                    request.files = FileUpload.parse_multipart(body, content_type)
                
                if (path, 'POST') in app_instance.api_routes:
                    self.handle_api_request('POST', path, request, response)
                else:
                    response.set_status(404)
                    response.json(JSONResponse.error("Not found", 404))
                    response.send(self)
            
            def do_PUT(self):
                parsed_path = urlparse(self.path)
                path = parsed_path.path
                
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length) if content_length > 0 else b''
                
                response = Response()
                request = Request(self, body)
                
                if not self._process_middlewares(request, response):
                    response.send(self)
                    return
                
                if (path, 'PUT') in app_instance.api_routes:
                    self.handle_api_request('PUT', path, request, response)
                else:
                    response.set_status(404)
                    response.json(JSONResponse.error("Not found", 404))
                    response.send(self)
            
            def do_DELETE(self):
                parsed_path = urlparse(self.path)
                path = parsed_path.path
                
                response = Response()
                request = Request(self)
                
                if not self._process_middlewares(request, response):
                    response.send(self)
                    return
                
                if (path, 'DELETE') in app_instance.api_routes:
                    self.handle_api_request('DELETE', path, request, response)
                else:
                    response.set_status(404)
                    response.json(JSONResponse.error("Not found", 404))
                    response.send(self)
            
            def serve_static_file(self, filename):
                """Serve static files with cache busting"""
                # Remove hash if present (file.abc123.js -> file.js)
                filename = re.sub(r'\.[a-f0-9]{6,}\.', '.', filename)
                
                filepath = Path(app_instance.static_dir) / filename
                
                if filepath.exists() and filepath.is_file():
                    mime_type, _ = mimetypes.guess_type(str(filepath))
                    mime_type = mime_type or 'application/octet-stream'
                    
                    self.send_response(200)
                    self.send_header('Content-type', mime_type)
                    self.send_header('Cache-Control', 'public, max-age=31536000')
                    self.end_headers()
                    
                    with open(filepath, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    self.send_error(404)
            
            def handle_api_request(self, method, path, request: Request, response: Response):
                """Handle API requests with middleware"""
                handler = app_instance.api_routes.get((path, method))
                if handler:
                    try:
                        # Call handler with request object
                        result = handler(request)
                        
                        # If handler returns Response object, use it
                        if isinstance(result, Response):
                            response = result
                        else:
                            response.json(result)
                        
                        self._process_response_middlewares(request, response)
                        response.send(self)
                    except Exception as e:
                        response.set_status(500)
                        response.json(JSONResponse.error(f"Internal server error: {str(e)}", 500))
                        response.send(self)
                else:
                    response.set_status(404)
                    response.json(JSONResponse.error("Not found", 404))
                    response.send(self)
            
            def log_message(self, format, *args):
                if app_instance.enable_logging:
                    super().log_message(format, *args)
        
        server = HTTPServer(('localhost', self.port), RequestHandler)
        print("=" * 60)
        print(f"🚀 Particle app running at http://localhost:{self.port}")
        print(f"📁 Static files: {self.static_dir}")
        print(f"🔌 API routes: {len(self.api_routes)}")
        print(f"🛡️  Middlewares: {len(self.middlewares)}")
        print(f"⚡ CORS: {'enabled' if self.enable_cors else 'disabled'}")
        print(f"📝 Logging: {'enabled' if self.enable_logging else 'disabled'}")
        print("Press Ctrl+C to stop")
        print("=" * 60)
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
            server.shutdown()

# ============= HIGHER-ORDER COMPONENTS =============

def with_props(**default_props):
    """HOC that provides default props"""
    def decorator(component_class):
        def wrapped(**props):
            merged_props = {**default_props, **props}
            return component_class(**merged_props)
        return wrapped
    return decorator

def with_store(component_class):
    """HOC that provides store access"""
    def wrapped(**props):
        store = use_store()
        return component_class(store=store, **props)
    return wrapped

def with_context(context: Context):
    """HOC that provides context value"""
    def decorator(component_class):
        def wrapped(**props):
            value = context.get_value()
            return component_class(context_value=value, **props)
        return wrapped
    return decorator

# ============= UTILITY FUNCTIONS =============

def merge_styles(*styles):
    """Merge multiple style dictionaries"""
    merged = {}
    for style in styles:
        if style:
            merged.update(style)
    return merged

def merge_classes(*classes):
    """Merge multiple class names"""
    return ' '.join(filter(None, classes))

def conditional_class(condition, true_class, false_class=''):
    """Conditional class name"""
    return true_class if condition else false_class