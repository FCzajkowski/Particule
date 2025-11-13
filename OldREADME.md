# Particule Framework Documentation

>[!WARNING]
>Particule is in its early stages of development. It might have bugs and issues. If any occur, please create one in 'Issues'.
>Thank you!


## Overview

Particule is a Python web framework that brings React-like component architecture and declarative UI building to Python. It allows you to create interactive web applications using familiar React patterns while writing pure Python code.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Concepts](#core-concepts)
- [State Management](#state-management)
- [Component Lifecycle](#component-lifecycle)
- [Event Handling](#event-handling)
- [Routing](#routing)
- [API Routes](#api-routes)
- [Animations](#animations)
- [Form Validation](#form-validation)
- [Examples](#examples)

## Installation

```bash
# Clone the repository
git clone https://github.com/FCzajkowski/PeHaPe.git
cd PeHaPe

# No dependencies required - uses Python standard library only
```

## Quick Start

Create a simple "Hello World" application:

```python
from lib import *

def HelloWorld():
    return div(
        {'style': {'padding': '20px'}},
        h1(None, text('Hello, World!')),
        p(None, text('Welcome to Particule Framework'))
    )

if __name__ == '__main__':
    app = App(HelloWorld)
    app.run(port=4000)
```

Visit `http://localhost:4000` to see your app running.

## Core Concepts

### Virtual DOM

Particule uses a virtual DOM system similar to React. Elements are created using Python functions and rendered to HTML:

```python
# Creating elements
div_element = div({'id': 'container'}, 
    h1(None, text('Title')),
    p(None, text('Paragraph'))
)

# Elements automatically render to HTML
html_output = div_element.to_html()
```

### Element Creation

Available HTML elements:

- **Layout**: `div`, `section`, `article`, `header`, `footer`, `nav`, `main`, `aside`
- **Text**: `h1-h6`, `p`, `span`, `strong`, `em`, `blockquote`, `code`, `pre`
- **Forms**: `form`, `input_field`, `textarea`, `select`, `option`, `label`, `button`
- **Lists**: `ul`, `ol`, `li`
- **Tables**: `table`, `thead`, `tbody`, `tr`, `th`, `td`
- **Media**: `img`, `a`
- **Other**: `br`, `hr`

### Props and Styling

Elements accept props as dictionaries:

```python
# Inline styles
div({
    'id': 'my-div',
    'className': 'container',
    'style': {
        'background': '#333',
        'padding': '20px',
        'border_radius': '8px'
    }
}, text('Content'))

# Attributes
img({
    'src': '/static/image.png',
    'alt': 'Description',
    'width': '300'
})
```

## State Management

### Simple State

Create reactive state using the `State` class:

```python
class Counter(Component):
    def __init__(self, **props):
        super().__init__(**props)
        self.count = self.use_state(0)
    
    def increment(self):
        self.count.set(self.count.get() + 1)
    
    def render(self):
        return div(None,
            h2(None, text(f'Count: {self.count.get()}')),
            button({'on_click': self.increment}, text('Increment'))
        )
```

### Computed State

Create derived state that updates automatically:

```python
class UserProfile(Component):
    def __init__(self, **props):
        super().__init__(**props)
        self.first_name = self.use_state('John')
        self.last_name = self.use_state('Doe')
        
        # Computed state
        self.full_name = self.use_computed(
            lambda: f"{self.first_name.get()} {self.last_name.get()}",
            self.first_name,
            self.last_name
        )
    
    def render(self):
        return div(None,
            text(f'Full Name: {self.full_name.get()}')
        )
```

### Global Store (Redux-like)

Manage global application state:

```python
# Create store
store = create_store({
    'user': None,
    'theme': 'dark',
    'notifications': []
})

# Add reducers
def set_user(state, action):
    return {**state, 'user': action['payload']}

store.add_reducer('SET_USER', set_user)

# Dispatch actions
store.dispatch({
    'type': 'SET_USER',
    'payload': {'name': 'Alice', 'id': 123}
})

# Subscribe to changes
def on_state_change():
    print('State updated:', store.get_state())

store.subscribe(on_state_change)
```

## Component Lifecycle

Components support lifecycle methods:

```python
class MyComponent(Component):
    def component_did_mount(self):
        """Called after component is rendered"""
        print('Component mounted')
    
    def component_will_unmount(self):
        """Called before component is removed"""
        print('Component will unmount')
    
    def component_did_update(self, prev_props, prev_state):
        """Called after props or state change"""
        print('Component updated')
    
    def render(self):
        return div(None, text('My Component'))
```

## Event Handling

### Using PyScript

Create interactive behaviors using the PyScript API:

```python
def TodoApp():
    return div(None,
        input_field({'id': 'todo-input', 'placeholder': 'Enter task'}),
        button({
            'on_click': lambda s: (
                s.append_item('todo-list', 
                    PyScript().get_value('todo-input')).
                clear_input('todo-input')
            )
        }, text('Add')),
        ul({'id': 'todo-list'})
    )
```

### Available PyScript Methods

```python
script = PyScript()

# DOM Manipulation
script.set_text('element-id', 'New text')
script.toggle_class('element-id', 'active')
script.add_class('element-id', 'highlight')
script.remove_class('element-id', 'hidden')
script.set_style('element-id', 'color', 'red')

# Navigation
script.navigate('/about')

# Utilities
script.toggle_visibility('element-id')
script.increment_counter('counter-id')
script.decrement_counter('counter-id')
script.append_item('list-id', '<span>Item</span>')
script.clear_input('input-id')

# Logging
script.log('Message', 'Value')
script.alert('Alert message')

# Custom JavaScript
script.custom('console.log("Custom JS")')
```

### Event Decorators

```python
@on_click
def handle_click(script):
    script.alert('Button clicked!')

@on_change
def handle_change(script):
    script.log('Input changed')

# Use in components
button({'on_click': handle_click}, text('Click me'))
```

## Routing

Create single-page applications with client-side routing:

```python
# Define routes
router = Router()

def HomePage():
    return div(None, h1(None, text('Home Page')))

def AboutPage():
    return div(None, h1(None, text('About Page')))

def NotFound():
    return div(None, h1(None, text('404 - Page Not Found')))

router.add_route('/', HomePage)
router.add_route('/about', AboutPage)
router.set_not_found(NotFound)

# Use router in app
app = App(HomePage)
app.use_router(router)
app.run()
```

Navigate between routes:

```python
# Using links
a({'href': '#/about'}, text('Go to About'))

# Using PyScript
button({
    'on_click': lambda s: s.navigate('/about')
}, text('Navigate'))
```

## API Routes

Create RESTful API endpoints:

```python
# Define API handler
def get_users(data):
    return {
        'users': [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ]
    }

def create_user(data):
    return {
        'success': True,
        'user': data
    }

# Register routes
app = App(HomePage)
app.add_api_route('/api/users', 'GET', get_users)
app.add_api_route('/api/users', 'POST', create_user)
app.run()
```

Call APIs from JavaScript:

```python
button({
    'on_click': """
        fetch('/api/users')
            .then(r => r.json())
            .then(data => console.log(data));
    """
}, text('Load Users'))
```

## Animations

Built-in animation helpers:

```python
from lib import Animation

# Fade in
button({
    'on_click': Animation.fade_in('my-element', duration_ms=500)
}, text('Fade In'))

# Fade out
button({
    'on_click': Animation.fade_out('my-element', duration_ms=500)
}, text('Fade Out'))

# Slide down
button({
    'on_click': Animation.slide_down('my-element', duration_ms=300)
}, text('Slide Down'))
```

## Form Validation

Validate form inputs:

```python
from lib import FormValidator

validator = FormValidator()

# Validation rules
is_valid_email = validator.email('user@example.com')  # True
is_required = validator.required('')  # False
is_long_enough = validator.min_length('password', 8)  # Depends on length
matches_pattern = validator.pattern('123-456', r'\d{3}-\d{3}')  # True
```

## Examples

### Counter Application

```python
def Counter():
    return div({'id': 'counter-app', 'style': {'padding': '20px'}},
        h2({'id': 'count'}, text('0')),
        button({
            'on_click': lambda s: s.increment_counter('count')
        }, text('+')),
        button({
            'on_click': lambda s: s.decrement_counter('count')
        }, text('-'))
    )

app = App(Counter)
app.run()
```

### Todo List

```python
def TodoList():
    return div({'style': {'padding': '20px'}},
        h1(None, text('Todo List')),
        div(None,
            input_field({
                'id': 'todo-input',
                'type': 'text',
                'placeholder': 'Enter a task'
            }),
            button({
                'on_click': lambda s: (
                    s.append_item('todo-list',
                        PyScript().get_value('todo-input')).
                    clear_input('todo-input')
                )
            }, text('Add Task'))
        ),
        ul({'id': 'todo-list', 'style': {'margin_top': '20px'}})
    )

app = App(TodoList)
app.run()
```

### Multi-Page Application

```python
def NavBar():
    return nav({'style': {'padding': '10px', 'background': '#333'}},
        a({'href': '#/', 'style': {'color': 'white', 'margin': '10px'}}, 
          text('Home')),
        a({'href': '#/about', 'style': {'color': 'white', 'margin': '10px'}}, 
          text('About')),
        a({'href': '#/contact', 'style': {'color': 'white', 'margin': '10px'}}, 
          text('Contact'))
    )

def Home():
    return div(None, NavBar(), h1(None, text('Home Page')))

def About():
    return div(None, NavBar(), h1(None, text('About Page')))

def Contact():
    return div(None, NavBar(), h1(None, text('Contact Page')))

router = Router()
router.add_route('/', Home)
router.add_route('/about', About)
router.add_route('/contact', Contact)

app = App(Home)
app.use_router(router)
app.run()
```

## Static Files

Serve static assets (images, CSS, JS):

```python
app = App(HomePage)
app.set_static_dir('static')  # Default is 'static'
app.run()
```

Access files at `/static/filename.ext`:

```python
img({'src': '/static/logo.png'})
```

## Higher-Order Components

### Default Props

```python
@with_props(color='blue', size='medium')
def Button(**props):
    return button({
        'style': {
            'background': props['color'],
            'padding': '10px' if props['size'] == 'medium' else '5px'
        }
    }, text(props.get('label', 'Click')))
```

### Store Connection

```python
@with_store
def UserDisplay(**props):
    store = props['store']
    state = store.get_state()
    return div(None, text(f"User: {state.get('user')}"))
```

## Configuration

### Server Configuration

```python
app = App(HomePage)
app.port = 8080  # Default is 6500
app.set_static_dir('assets')
app.run(port=8080)  # Override in run() as well
```

## Best Practices

1. **Component Organization**: Keep components small and focused on a single responsibility
2. **State Management**: Use local state for component-specific data, global store for shared data
3. **Event Handlers**: Use PyScript for simple interactions, custom JavaScript for complex logic
4. **Styling**: Prefer inline styles for component-specific styling, external CSS for global styles
5. **Performance**: Minimize unnecessary re-renders by keeping state minimal

## Contributing

Contributions are welcome! Visit the [GitHub repository](https://github.com/FCzajkowski/PeHaPe) to:

- Report bugs
- Suggest features
- Submit pull requests
- Review documentation

## License

Check the repository for license information.

## Links

- **GitHub**: [https://github.com/FCzajkowski](https://github.com/FCzajkowski)
- **Documentation**: [https://github.com/FCzajkowski/PeHaPe](https://github.com/FCzajkowski/PeHaPe)

---

Built with ❤️ using Python


