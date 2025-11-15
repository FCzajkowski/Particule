"""Component system with lifecycle and hooks"""

from typing import Callable, Dict
from .state_management import State, Ref, ComputedState, Context


class Component:
    """Base component class with lifecycle methods"""
    def __init__(self, **props):
        self.props = props
        self.state = {}
        self._is_mounted = False
        self._cleanup_handlers = []
        self._refs = {}
    
    def use_state(self, initial_value):
        """Hook for state management"""
        return State(initial_value)
    
    def use_ref(self, initial_value=None):
        """Hook for mutable ref"""
        return Ref(initial_value)
    
    def use_computed(self, compute_fn: Callable, *dependencies: State):
        """Hook for computed/derived state"""
        return ComputedState(compute_fn, *dependencies)
    
    def use_context(self, context: Context):
        """Hook for context consumption"""
        return context.get_value()
    
    def component_did_mount(self):
        """Called after component is rendered"""
        pass
    
    def component_will_unmount(self):
        """Called before component is removed"""
        pass
    
    def component_did_update(self, prev_props: Dict, prev_state: Dict):
        """Called after props or state change"""
        pass
    
    def _mount(self):
        """Internal mount lifecycle"""
        if not self._is_mounted:
            self._is_mounted = True
            self.component_did_mount()
    
    def _unmount(self):
        """Internal unmount lifecycle"""
        if self._is_mounted:
            self._is_mounted = False
            for cleanup in self._cleanup_handlers:
                cleanup()
            self.component_will_unmount()
    
    def render(self):
        """Must be implemented by child classes"""
        raise NotImplementedError("Component must implement render method")
