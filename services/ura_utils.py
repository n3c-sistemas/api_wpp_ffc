
import re

class UraUtils:
    def __init__(self):
        self.sessions = {}
        
    def normalize_input(self, text):
        if not text:
            return ''
        return text.strip().lower()
    
    def normalize_input_upper(self, text):
        if not text:
            return ''
        return text.strip().upper()

    def normalize_cpf(self, cpf_text):
        digits = re.sub(r'\D', '', cpf_text)
        if len(digits) != 11:
            return None
        return f'{digits[0:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:11]}'
    
    def build_text_payload(self, body_text):
        return {
            'type': 'text',
            'text': {'body': body_text}
        }

    def build_button_payload(self, body_text, buttons):
        return {
            'type': 'interactive',
            'interactive': {
                'type': 'button',
                'body': {'text': body_text},
                'action': {'buttons': buttons}
            }
        }