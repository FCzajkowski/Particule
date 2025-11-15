"""Form validation and creation utilities"""

import re
from typing import List, Dict, Callable
from .events_animations import on_submit_prevent
from .vdom import form, label, input_field, button, text, br


class FormValidator:
    """Form validation utilities"""
    
    @staticmethod
    def required(value):
        return bool(value and str(value).strip())
    
    @staticmethod
    def email(value):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return bool(re.match(pattern, str(value)))
    
    @staticmethod
    def min_length(value, length):
        return len(str(value)) >= length
    
    @staticmethod
    def max_length(value, length):
        return len(str(value)) <= length
    
    @staticmethod
    def pattern(value, regex_pattern):
        return bool(re.match(regex_pattern, str(value)))
    
    @staticmethod
    def phone(value):
        """Validate phone number"""
        pattern = r'^[\d\s\-\+\(\)]+'
        return bool(re.match(pattern, str(value)))
    
    @staticmethod
    def url(value):
        """Validate URL"""
        pattern = r'^https?://[^\s]+'
        return bool(re.match(pattern, str(value)))


def create_form_component(fields: List[Dict], on_submit: Callable):
    """Create a form component with automatic validation"""
    def FormComponent():
        field_elements = []
        for field in fields:
            field_id = field.get('id', field['name'])
            field_type = field.get('type', 'text')
            field_label = field.get('label', field['name'])
            required = field.get('required', False)
            
            field_elements.extend([
                label({'for': field_id}, text(field_label)),
                input_field({
                    'type': field_type,
                    'id': field_id,
                    'name': field['name'],
                    'required': 'required' if required else None
                }),
                br()
            ])
        
        return form(
            {'on_submit': on_submit_prevent(lambda s: (s.custom(on_submit), s))},
            *field_elements,
            button({'type': 'submit'}, text('Submit'))
        )
    
    return FormComponent
