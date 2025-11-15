"""Event handling and animations"""

from typing import Callable


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
