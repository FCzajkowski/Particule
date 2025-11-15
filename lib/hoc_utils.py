"""Higher-order components and utility functions"""

from .state_management import Context


def with_props(**default_props):
    """HOC that provides default props"""
    def decorator(component_class):
        def wrapped(**props):
            merged_props = {**default_props, **props}
            return component_class(**merged_props)
        return wrapped
    return decorator


def with_store(component_class):
    """HOC that provides store access"""
    def wrapped(**props):
        from .state_management import use_store
        store = use_store()
        return component_class(store=store, **props)
    return wrapped


def with_context(context: Context):
    """HOC that provides context value"""
    def decorator(component_class):
        def wrapped(**props):
            value = context.get_value()
            return component_class(context_value=value, **props)
        return wrapped
    return decorator


def merge_styles(*styles):
    """Merge multiple style dictionaries"""
    merged = {}
    for style in styles:
        if style:
            merged.update(style)
    return merged


def merge_classes(*classes):
    """Merge multiple class names"""
    return ' '.join(filter(None, classes))


def conditional_class(condition, true_class, false_class=''):
    """Conditional class name"""
    return true_class if condition else false_class
