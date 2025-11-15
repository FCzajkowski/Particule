"""State management system with hooks, store, and context"""

from typing import Callable, Dict, List
from functools import wraps


class State:
    """State management similar to React useState"""
    def __init__(self, initial_value):
        self._value = initial_value
        self._listeners = []
    
    def get(self):
        return self._value
    
    def set(self, new_value):
        self._value = new_value
        for listener in self._listeners:
            listener()
    
    def subscribe(self, listener):
        self._listeners.append(listener)


class Ref:
    """Mutable reference that doesn't trigger re-renders"""
    def __init__(self, initial_value=None):
        self.current = initial_value


class ComputedState:
    """Derived state that updates automatically when dependencies change"""
    def __init__(self, compute_fn: Callable, *dependencies: State):
        self.compute_fn = compute_fn
        self.dependencies = dependencies
        self._cached_value = None
        self._is_dirty = True
        
        for dep in dependencies:
            dep.subscribe(self._mark_dirty)
    
    def _mark_dirty(self):
        self._is_dirty = True
    
    def get(self):
        if self._is_dirty:
            self._cached_value = self.compute_fn()
            self._is_dirty = False
        return self._cached_value


class Store:
    """Global store for state management (Redux-like) with persistence"""
    def __init__(self, initial_state: Dict, persist_keys: List[str] = None):
        self._state = initial_state
        self._listeners = []
        self._reducers = {}
        self._persist_keys = persist_keys or []
        self._middleware = []
        self._logger_enabled = False
    
    def get_state(self):
        return self._state.copy()
    
    def subscribe(self, listener: Callable):
        self._listeners.append(listener)
        return lambda: self._listeners.remove(listener)
    
    def dispatch(self, action: Dict):
        """Dispatch an action to update state"""
        prev_state = self._state.copy()
        action_type = action.get('type')
        
        # Log action
        if self._logger_enabled:
            print(f"[STORE] Action: {action_type}")
            print(f"[STORE] Payload: {action}")
        
        # Process middleware
        for mw in self._middleware:
            action = mw(self._state, action)
            if action is None:
                return
        
        if action_type in self._reducers:
            self._state = self._reducers[action_type](self._state, action)
            
            # Log state change
            if self._logger_enabled:
                print(f"[STORE] Prev State: {prev_state}")
                print(f"[STORE] Next State: {self._state}")
            
            # Persist if needed
            self._persist()
            
            for listener in self._listeners:
                listener()
    
    def add_reducer(self, action_type: str, reducer: Callable):
        """Register a reducer for an action type"""
        self._reducers[action_type] = reducer
    
    def add_middleware(self, middleware: Callable):
        """Add middleware (state, action) => action"""
        self._middleware.append(middleware)
    
    def enable_logger(self):
        """Enable action/state logging"""
        self._logger_enabled = True
    
    def _persist(self):
        """Persist specified keys to localStorage (client-side only)"""
        if self._persist_keys:
            persist_data = {k: self._state.get(k) for k in self._persist_keys if k in self._state}
            # This would be handled client-side with localStorage
            pass


# Global store instance
_global_store = None


def create_store(initial_state: Dict, persist_keys: List[str] = None) -> Store:
    """Create a global store"""
    global _global_store
    _global_store = Store(initial_state, persist_keys)
    return _global_store


def use_store() -> Store:
    """Get the global store"""
    return _global_store


class Context:
    """Context for sharing data across component tree"""
    def __init__(self, default_value=None):
        self._value = default_value
        self._consumers = []
    
    def provide(self, value):
        """Set context value"""
        self._value = value
        for consumer in self._consumers:
            consumer(value)
    
    def consume(self, callback):
        """Subscribe to context changes"""
        self._consumers.append(callback)
        callback(self._value)
        return lambda: self._consumers.remove(callback)
    
    def get_value(self):
        """Get current context value"""
        return self._value


def create_context(default_value=None):
    """Create a new context"""
    return Context(default_value)
