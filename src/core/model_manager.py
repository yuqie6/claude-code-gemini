from src.core.config import config

class ModelManager:
    def __init__(self, config):
        self.config = config
        # Project now only supports Gemini API - simplified model mapping
        if not self.config.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required. Project only supports Gemini API.")

        # Claude Models -> Gemini mapping
        self._MODEL_MAP = {
            # Claude 4 Models
            'claude-4-opus-20250514': {'api_type': 'gemini', 'model_name': self.config.big_model},
            'claude-4-opus': {'api_type': 'gemini', 'model_name': self.config.big_model},
            'claude-4-haiku': {'api_type': 'gemini', 'model_name': self.config.small_model},
            'claude-4-sonnet': {'api_type': 'gemini', 'model_name': self.config.big_model},

            # Claude 3.5 Models
            'claude-3-5-sonnet-20241022': {'api_type': 'gemini', 'model_name': self.config.big_model},
            'claude-3-5-haiku-20241022': {'api_type': 'gemini', 'model_name': self.config.small_model},

            # Claude 3 Models
            'claude-3-opus-20240229': {'api_type': 'gemini', 'model_name': self.config.big_model},
            'claude-3-sonnet-20240229': {'api_type': 'gemini', 'model_name': self.config.big_model},
            'claude-3-haiku-20240307': {'api_type': 'gemini', 'model_name': self.config.small_model},

            # Native Gemini Models (direct mapping)
            'gemini-1.5-pro-latest': {'api_type': 'gemini', 'model_name': 'gemini-1.5-pro-latest'},
            'gemini-1.5-flash-latest': {'api_type': 'gemini', 'model_name': 'gemini-1.5-flash-latest'},
            'gemini-2.0-flash-exp': {'api_type': 'gemini', 'model_name': 'gemini-2.0-flash-exp'},
            'gemini-2.5-pro': {'api_type': 'gemini', 'model_name': 'gemini-2.5-pro'},
            'gemini-2.5-flash': {'api_type': 'gemini', 'model_name': 'gemini-2.5-flash'},
            'gemini-1.0-pro': {'api_type': 'gemini', 'model_name': 'gemini-1.0-pro'},
        }

    def get_model_info(self, claude_model: str) -> dict:
        """Get API type and mapped model name for a given Claude model. Only supports Gemini API."""
        # Direct mapping for known Gemini models
        if claude_model.startswith("gemini-"):
            return {'api_type': 'gemini', 'model_name': claude_model}

        # Mapping for Claude models
        info = self._MODEL_MAP.get(claude_model)
        if info:
            return info

        # Fallback for unknown Claude models based on keywords - always map to Gemini
        model_lower = claude_model.lower()
        if 'haiku' in model_lower:
            return {'api_type': 'gemini', 'model_name': self.config.small_model}
        elif 'sonnet' in model_lower or 'opus' in model_lower:
            return {'api_type': 'gemini', 'model_name': self.config.big_model}

        # Default to big Gemini model for any unknown model
        return {'api_type': 'gemini', 'model_name': self.config.big_model}

model_manager = ModelManager(config)