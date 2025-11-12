from lib import *


def HomePage():
    """Main landing page for Particule Framework"""
    return div(
        {'style': {
            'min_height': '100vh',
            'display': 'flex',
            'align_items': 'center',
            'justify_content': 'center',
            'background': '#332F2F'
        }},
        
        div(
            {'style': {
                'text_align': 'center',
                'background': '#282424',
                'padding': '60px 40px',
                'border_radius': '10px',
                'box_shadow': '0 4px 20px rgba(0,0,0,0.3)'
            }},
            
            # Logo
            img({
                'src': '/static/Logo.svg',
                'alt': 'Particule Logo',
                'style': {
                    'width': '150px',
                    'height': '150px',
                    'margin_bottom': '30px'
                }
            }),
            
            # Thank you message
            p(
                {'style': {
                    'font_size': '24px',
                    'color': '#e0e0e0',
                    'margin_bottom': '30px'
                }},
                text('Thank you for choosing Particule!')
            ),
            
            # Links
            div(
                {'style': {
                    'display': 'flex',
                    'gap': '20px',
                    'justify_content': 'center'
                }},
                
                a(
                    {
                        'href': 'https://github.com/FCzajkowski',
                        'target': '_blank',
                        'style': {
                            'color': '#6fa3ef',
                            'text_decoration': 'none',
                            'font_size': '18px',
                            'transition': '250ms'
                        }
                    },
                    text('GitHub')
                ),
                
                a(
                    {
                        'href': 'https://github.com/FCzajkowski/PeHaPe',
                        'target': '_blank',
                        'style': {
                            'color': '#6fa3ef',
                            'text_decoration': 'none',
                            'font_size': '18px',
                            'transition': '250ms'
                        }
                    },
                    text('Documentation')
                )
            )
        ),
        
        create_element('style', None, text("""
            a:hover {
                color: #3b82f6 !important;
            }
        """))
    )

if __name__ == '__main__':
    app = App(HomePage)
    app.set_static_dir('static')
    app.run(port=4000)