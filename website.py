from lib.lib import * 

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
app.run(port=5000)