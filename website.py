from lib.lib import *

# ============= TODO LIST COMPONENT (FIXED) =============

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
                    s.append_item('todo-list', s.get_value('todo-input')),
                    s.clear_input('todo-input')
                )
            }, text('Add Task'))
        ),
        ul({'id': 'todo-list', 'style': {'margin_top': '20px'}})
    )

# ============= ROUTING EXAMPLE =============

def Home():
    return div({'style': {'padding': '20px'}},
        h1(None, text('Home Page')),
        p(None, text('Welcome to the Particule demo!')),
        button({
            'on_click': lambda s: s.navigate('/about')
        }, text('Go to About')),
        button({
            'on_click': lambda s: s.navigate('/todo'),
            'style': {'margin_left': '10px'}
        }, text('Go to Todo List'))
    )

def About():
    return div({'style': {'padding': '20px'}},
        h1(None, text('About Page')),
        p(None, text('This is a Particule framework demo.')),
        button({
            'on_click': lambda s: s.navigate('/')
        }, text('Go to Home')),
        button({
            'on_click': lambda s: s.navigate('/todo'),
            'style': {'margin_left': '10px'}
        }, text('Go to Todo List'))
    )

def TodoPage():
    return div({'style': {'padding': '20px'}},
        h1(None, text('Todo List')),
        div({'style': {'margin_bottom': '10px'}},
            button({
                'on_click': lambda s: s.navigate('/')
            }, text('Home')),
            button({
                'on_click': lambda s: s.navigate('/about'),
                'style': {'margin_left': '10px'}
            }, text('About'))
        ),
        hr(),
        div({'style': {'margin_top': '20px'}},
            input_field({
                'id': 'todo-input',
                'type': 'text',
                'placeholder': 'Enter a task'
            }),
            button({
                'on_click': lambda s: (
                    s.append_item('todo-list', s.get_value('todo-input')),
                    s.clear_input('todo-input')
                ),
                'style': {'margin_left': '10px'}
            }, text('Add Task'))
        ),
        ul({'id': 'todo-list', 'style': {'margin_top': '20px'}})
    )

def NotFound():
    return div({'style': {'padding': '20px', 'text_align': 'center'}},
        h1(None, text('404 - Page Not Found')),
        p(None, text('The page you are looking for does not exist.')),
        button({
            'on_click': lambda s: s.navigate('/')
        }, text('Go Home'))
    )

# ============= SETUP ROUTER =============

router = Router()
router.add_route('/', Home)
router.add_route('/about', About)
router.add_route('/todo', TodoPage)
router.set_not_found(NotFound)

# ============= RUN APP =============

# Without routing (just todo list)
# app = App(TodoList)
# app.run()

# With routing
app = App(Home)  # Start with Home
app.use_router(router)
app.run()