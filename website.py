from lib import *

def DefaultSite():
    # Inline style tag for animations
    style_tag = """
    <style>
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        body {
            margin: 0;
            padding: 0;
        }
    </style>
    """
    
    return div({
        'style': {
            'min_height': '100vh',
            'display': 'flex',
            'flex_direction': 'column',
            'align_items': 'center',
            'justify_content': 'center',
            'background': '#000000',
            'font_family': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
            'padding': '20px'
        }
    },
        # Logo placeholder
        div({
            'style': {
                'width': '180px',
                'height': '180px',
                'background': '#ffffff',
                'border_radius': '50%',
                'display': 'flex',
                'align_items': 'center',
                'justify_content': 'center',
                'font_size': '4rem',
                'font_weight': '700',
                'margin_bottom': '40px',
                'color': '#000000'
            }
        }, text('P')),
        
        # Title
        h1({
            'style': {
                'color': '#ffffff',
                'font_size': '2.5rem',
                'font_weight': '400',
                'margin': '0 0 20px 0',
                'text_align': 'center'
            }
        }, text('Particule')),
        
        # Thank you message
        p({
            'style': {
                'color': '#999999',
                'font_size': '1.1rem',
                'margin': '0 0 60px 0',
                'text_align': 'center',
                'font_weight': '300'
            }
        }, text('Thank you for choosing Particule <3')),
        
        # Buttons container
        div({
            'style': {
                'display': 'flex',
                'gap': '20px'
            }
        },
            # GitHub button
            a({
                'href': 'https://github.com/FCzajkowski/Particule',
                'target': '_blank',
                'style': {
                    'background': 'transparent',
                    'color': '#ffffff',
                    'padding': '12px 32px',
                    'border': '1px solid #ffffff',
                    'border_radius': '4px',
                    'text_decoration': 'none',
                    'font_weight': '400',
                    'font_size': '1rem',
                    'transition': 'all 0.2s ease',
                    'display': 'inline_block'
                },
                'onmouseover': "this.style.background='#ffffff'; this.style.color='#000000'",
                'onmouseout': "this.style.background='transparent'; this.style.color='#ffffff'"
            }, text('GitHub')),
            
            # Documentation button
            a({
                'href': 'https://github.com/FCzajkowski/Particule',
                'target': '_blank',
                'style': {
                    'background': 'transparent',
                    'color': '#ffffff',
                    'padding': '12px 32px',
                    'border': '1px solid #ffffff',
                    'border_radius': '4px',
                    'text_decoration': 'none',
                    'font_weight': '400',
                    'font_size': '1rem',
                    'transition': 'all 0.2s ease',
                    'display': 'inline_block'
                },
                'onmouseover': "this.style.background='#ffffff'; this.style.color='#000000'",
                'onmouseout': "this.style.background='transparent'; this.style.color='#ffffff'"
            }, text('Documentation'))
        )
    )


# Run the app
if __name__ == '__main__':
    app = App(DefaultSite)
    app.run(port=4000)