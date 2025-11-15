"""
Particule - A Python framework for building interactive web applications
"""

# Response helpers
from .responses import JSONResponse

# Cookies and sessions
from .cookies_sessions import Cookie, Session

# Middleware
from .middleware import (
    Request,
    Response,
    Middleware,
    CORSMiddleware,
    LoggingMiddleware,
    AuthMiddleware,
)

# File upload
from .file_upload import FileUpload

# Client helpers
from .client_helpers import create_fetch_helpers, create_input_mask_js

# State management
from .state_management import (
    State,
    Ref,
    ComputedState,
    Store,
    Context,
    create_store,
    use_store,
    create_context,
)

# Component system
from .component import Component

# Events and animations
from .events_animations import (
    JSBuilder,
    PyScript,
    on_click,
    on_click_prevent,
    on_submit_prevent,
    Animation,
)

# Routing
from .routing import Router

# Virtual DOM
from .vdom import (
    Element,
    create_element,
    text,
    fragment,
    # SVG elements
    svg,
    path,
    circle,
    rect,
    line,
    polygon,
    ellipse,
    g,
    # HTML elements
    div,
    h1,
    h2,
    h3,
    h4,
    h5,
    h6,
    p,
    button,
    input_field,
    textarea,
    select,
    option,
    label,
    form,
    span,
    ul,
    ol,
    li,
    img,
    a,
    br,
    hr,
    section,
    article,
    header,
    footer,
    nav,
    main,
    aside,
    table,
    thead,
    tbody,
    tr,
    th,
    td,
    code,
    pre,
    strong,
    em,
    blockquote,
    canvas,
    video,
    audio,
)

# Form validation
from .form_validation import FormValidator, create_form_component

# App
from .app import App

# HOCs and utilities
from .hoc_utils import (
    with_props,
    with_store,
    with_context,
    merge_styles,
    merge_classes,
    conditional_class,
)

__version__ = "1.0.0"
__author__ = "Particule Team"

__all__ = [
    # Response helpers
    "JSONResponse",
    # Cookies and sessions
    "Cookie",
    "Session",
    # Middleware
    "Request",
    "Response",
    "Middleware",
    "CORSMiddleware",
    "LoggingMiddleware",
    "AuthMiddleware",
    # File upload
    "FileUpload",
    # Client helpers
    "create_fetch_helpers",
    "create_input_mask_js",
    # State management
    "State",
    "Ref",
    "ComputedState",
    "Store",
    "Context",
    "create_store",
    "use_store",
    "create_context",
    # Component system
    "Component",
    # Events and animations
    "JSBuilder",
    "PyScript",
    "on_click",
    "on_click_prevent",
    "on_submit_prevent",
    "Animation",
    # Routing
    "Router",
    # Virtual DOM
    "Element",
    "create_element",
    "text",
    "fragment",
    # SVG elements
    "svg",
    "path",
    "circle",
    "rect",
    "line",
    "polygon",
    "ellipse",
    "g",
    # HTML elements
    "div",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "p",
    "button",
    "input_field",
    "textarea",
    "select",
    "option",
    "label",
    "form",
    "span",
    "ul",
    "ol",
    "li",
    "img",
    "a",
    "br",
    "hr",
    "section",
    "article",
    "header",
    "footer",
    "nav",
    "main",
    "aside",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "code",
    "pre",
    "strong",
    "em",
    "blockquote",
    "canvas",
    "video",
    "audio",
    # Form validation
    "FormValidator",
    "create_form_component",
    # App
    "App",
    # HOCs and utilities
    "with_props",
    "with_store",
    "with_context",
    "merge_styles",
    "merge_classes",
    "conditional_class",
]
