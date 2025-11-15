"""SPA routing system with parameters and transitions"""

import json
from typing import Callable
from urllib.parse import unquote


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
        from .vdom import Element
        
        routes_html = {}
        for path, component in self.routes.items():
            comp_instance = component()
            from .component import Component
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
