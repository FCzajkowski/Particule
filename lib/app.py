"""Main application class with server and middleware"""

import re
import json
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from typing import Callable, List

from .middleware import Request, Response, Middleware, CORSMiddleware, LoggingMiddleware, AuthMiddleware
from .responses import JSONResponse
from .client_helpers import create_fetch_helpers, create_input_mask_js
from .file_upload import FileUpload
from .routing import Router
from .component import Component
from .vdom import Element


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
