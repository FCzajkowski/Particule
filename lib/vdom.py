"""Virtual DOM implementation with element rendering"""

import html
from typing import Dict


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
                    from .events_animations import PyScript
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
