from typing import Any, Callable, Dict, List, Union, Optional
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid
import os
import mimetypes
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# ============= STATE MANAGEMENT =============

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

class ComputedState:
    """Derived state that updates automatically when dependencies change"""
    def __init__(self, compute_fn: Callable, *dependencies: State):
        self.compute_fn = compute_fn
        self.dependencies = dependencies
        self._cached_value = None
        self._is_dirty = True
        
        # Subscribe to all dependencies
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
    """Global store for state management (Redux-like)"""
    def __init__(self, initial_state: Dict):
        self._state = initial_state
        self._listeners = []
        self._reducers = {}
    
    def get_state(self):
        return self._state.copy()
    
    def subscribe(self, listener: Callable):
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)
    
    def dispatch(self, action: Dict):
        """Dispatch an action to update state"""
        action_type = action.get('type')
        if action_type in self._reducers:
            self._state = self._reducers[action_type](self._state, action)
            for listener in self._listeners:
                listener()
    
    def add_reducer(self, action_type: str, reducer: Callable):
        """Register a reducer for an action type"""
        self._reducers[action_type] = reducer

# Global store instance
_global_store = None

def create_store(initial_state: Dict) -> Store:
    """Create a global store"""
    global _global_store
    _global_store = Store(initial_state)
    return _global_store

def use_store() -> Store:
    """Get the global store"""
    return _global_store

# ============= COMPONENT LIFECYCLE =============

class Component:
    """Base component class with lifecycle methods"""
    def __init__(self, **props):
        self.props = props
        self.state = {}
        self._is_mounted = False
        self._cleanup_handlers = []
    
    def use_state(self, initial_value):
        """Hook for state management"""
        return State(initial_value)
    
    def use_computed(self, compute_fn: Callable, *dependencies: State):
        """Hook for computed/derived state"""
        return ComputedState(compute_fn, *dependencies)
    
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
    
    def append_item(self, list_id, item_html):
        js_code = f"""
        let list = document.getElementById('{list_id}');
        let li = document.createElement('li');
        li.innerHTML = '{item_html}';
        list.appendChild(li);
        """
        self.statements.append(js_code)
        return self
    
    def clear_input(self, input_id):
        self.statements.append(f"document.getElementById('{input_id}').value = ''")
        return self
    
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

def on_change(script_func):
    script = PyScript()
    script_func(script)
    return script.to_js()

def on_submit(script_func):
    script = PyScript()
    script_func(script)
    return script.to_js()

def on_mouse_over(script_func):
    script = PyScript()
    script_func(script)
    return script.to_js()

def on_mouse_out(script_func):
    script = PyScript()
    script_func(script)
    return script.to_js()

def on_focus(script_func):
    script = PyScript()
    script_func(script)
    return script.to_js()

def on_blur(script_func):
    script = PyScript()
    script_func(script)
    return script.to_js()

def on_key_down(script_func):
    script = PyScript()
    script_func(script)
    return script.to_js()

def on_key_up(script_func):
    script = PyScript()
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

# ============= ROUTING =============

class Router:
    """Simple SPA router"""
    def __init__(self):
        self.routes = {}
        self.not_found = None
    
    def add_route(self, path: str, component: Callable):
        """Register a route"""
        self.routes[path] = component
    
    def set_not_found(self, component: Callable):
        """Set 404 component"""
        self.not_found = component
    
    def get_route_js(self):
        """Generate JavaScript router code"""
        routes_json = json.dumps({path: f"route_{i}" for i, path in enumerate(self.routes.keys())})
        
        return f"""
        <script>
        function renderRoute() {{
            const hash = window.location.hash.slice(1) || '/';
            const app = document.getElementById('app');
            
            // Simple route matching
            const routes = {routes_json};
            
            if (routes[hash]) {{
                // In a real implementation, this would re-render the component
                console.log('Navigating to:', hash);
            }} else {{
                console.log('Route not found:', hash);
            }}
        }}
        
        window.addEventListener('hashchange', renderRoute);
        window.addEventListener('load', renderRoute);
        </script>
        """

# ============= VIRTUAL DOM =============

class Element:
    """Represents a virtual DOM element"""
    def __init__(self, tag: str, props: Dict = None, *children):
        self.tag = tag
        self.props = props or {}
        self.children = list(children) if children else []
    
    def to_html(self) -> str:
        if self.tag == 'text':
            content = str(self.props.get('content', ''))
            content = content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            return content
        
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
        
        # Build attributes
        attrs = []
        for key, value in self.props.items():
            if key == 'key':
                continue
            attr_name = key.replace('_', '-')
            if key == 'className':
                attr_name = 'class'
            attrs.append(f'{attr_name}="{value}"')
        
        attrs_str = ' ' + ' '.join(attrs) if attrs else ''
        
        # Self-closing tags
        if self.tag in ['img', 'br', 'hr', 'input', 'meta', 'link']:
            return f'<{self.tag}{attrs_str} />'
        
        # Render children
        children_html = ''.join(
            child.to_html() if isinstance(child, Element) else str(child)
            for child in self.children
        )
        
        return f'<{self.tag}{attrs_str}>{children_html}</{self.tag}>'

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

# ============= FORM VALIDATION =============

class FormValidator:
    """Form validation utilities"""
    
    @staticmethod
    def required(value):
        return bool(value and str(value).strip())
    
    @staticmethod
    def email(value):
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(value)))
    
    @staticmethod
    def min_length(value, length):
        return len(str(value)) >= length
    
    @staticmethod
    def max_length(value, length):
        return len(str(value)) <= length
    
    @staticmethod
    def pattern(value, regex_pattern):
        import re
        return bool(re.match(regex_pattern, str(value)))

# ============= APP CLASS =============

class App:
    """Main application class with enhanced server"""
    def __init__(self, root_component: Callable):
        self.root_component = root_component
        self.port = 6500
        self.static_dir = 'static'
        self.api_routes = {}
        self.router = None
    
    def add_api_route(self, path: str, method: str, handler: Callable):
        """Add an API route"""
        self.api_routes[(path, method)] = handler
    
    def set_static_dir(self, directory: str):
        """Set static files directory"""
        self.static_dir = directory
    
    def use_router(self, router: Router):
        """Enable routing"""
        self.router = router
    
    def render_to_html(self) -> str:
        component_instance = self.root_component()
        if isinstance(component_instance, Component):
            rendered = component_instance.render()
        else:
            rendered = component_instance
        
        body_html = rendered.to_html() if isinstance(rendered, Element) else str(rendered)
        
        router_js = self.router.get_route_js() if self.router else ""
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PyReact App</title>
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
    {router_js}
</body>
</html>"""
    
    def run(self, port: int = None):
        """Start the development server"""
        if port:
            self.port = port
        
        app_instance = self
        
        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed_path = urlparse(self.path)
                path = parsed_path.path
                
                # Serve static files
                if path.startswith('/static/'):
                    self.serve_static_file(path[8:])
                # Serve API routes
                elif (path, 'GET') in app_instance.api_routes:
                    self.handle_api_request('GET', path)
                # Serve main app
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    html = app_instance.render_to_html()
                    self.wfile.write(html.encode())
            
            def do_POST(self):
                parsed_path = urlparse(self.path)
                path = parsed_path.path
                
                if (path, 'POST') in app_instance.api_routes:
                    self.handle_api_request('POST', path)
                else:
                    self.send_error(404)
            
            def serve_static_file(self, filename):
                """Serve static files"""
                filepath = Path(app_instance.static_dir) / filename
                
                if filepath.exists() and filepath.is_file():
                    mime_type, _ = mimetypes.guess_type(str(filepath))
                    mime_type = mime_type or 'application/octet-stream'
                    
                    self.send_response(200)
                    self.send_header('Content-type', mime_type)
                    self.end_headers()
                    
                    with open(filepath, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    self.send_error(404)
            
            def handle_api_request(self, method, path):
                """Handle API requests"""
                handler = app_instance.api_routes.get((path, method))
                if handler:
                    content_length = int(self.headers.get('Content-Length', 0))
                    body = self.rfile.read(content_length) if content_length > 0 else b''
                    
                    try:
                        data = json.loads(body) if body else {}
                    except:
                        data = {}
                    
                    response = handler(data)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_error(404)
            
            def log_message(self, format, *args):
                pass
        
        server = HTTPServer(('localhost', self.port), RequestHandler)
        print(f"🚀 PyReact app running at http://localhost:{self.port}")
        print(f"📁 Static files served from: {self.static_dir}")
        print(f"🔌 API routes: {list(self.api_routes.keys())}")
        print(f"Press Ctrl+C to stop the server")
        
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
