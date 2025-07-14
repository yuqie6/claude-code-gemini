import os
import sys

# Configuration
class Config:
    def __init__(self):
        # Project now only supports Gemini API
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")

        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required. Project only supports Gemini API.")

        self.gemini_base_url = os.environ.get("GEMINI_BASE_URL")  # For custom Gemini endpoints
        self.host = os.environ.get("HOST", "0.0.0.0")
        self.port = int(os.environ.get("PORT", "8082"))
        self.log_level = os.environ.get("LOG_LEVEL", "INFO")
        self.max_tokens_limit = int(os.environ.get("MAX_TOKENS_LIMIT", "4096"))
        self.min_tokens_limit = int(os.environ.get("MIN_TOKENS_LIMIT", "100"))
        
        # Connection settings
        self.request_timeout = int(os.environ.get("REQUEST_TIMEOUT", "90"))
        self.max_retries = int(os.environ.get("MAX_RETRIES", "2"))
        
        # Model settings - BIG and SMALL models (Gemini defaults)
        self.big_model = os.environ.get("BIG_MODEL", "gemini-2.5-pro")
        self.small_model = os.environ.get("SMALL_MODEL", "gemini-2.5-flash")

        # Thinking settings for Gemini 2.5 models - separate for big/small models
        self.big_model_thinking_budget = int(os.environ.get("BIG_MODEL_THINKING_BUDGET", "5000"))    # Pro models: conservative budget (was -1)
        self.small_model_thinking_budget = int(os.environ.get("SMALL_MODEL_THINKING_BUDGET", "1000"))  # Flash models: conservative budget
        self.enable_thinking_by_default = os.environ.get("ENABLE_THINKING_BY_DEFAULT", "false").lower() == "true"  # Changed default to false

        # Cache settings - Client-side content caching to reduce token usage
        self.enable_content_cache = os.environ.get("ENABLE_CONTENT_CACHE", "false").lower() == "true"
        self.cache_min_chars = int(os.environ.get("CACHE_MIN_CHARS", "4096"))
        self.cache_ttl_hours = int(os.environ.get("CACHE_TTL_HOURS", "24"))
        
    def validate_api_key(self):
        """Basic Gemini API key validation"""
        if not self.gemini_api_key:
            return False
        # Basic format check for Gemini API keys (they typically start with 'AI')
        return len(self.gemini_api_key) > 10  # Basic length check

try:
    config = Config()
    # 显示配置信息
    gemini_status = "✓" if config.gemini_api_key else "✗"

    print("🔧 Configuration loaded:")
    print(f"   Gemini API: {gemini_status} | Base URL: {config.gemini_base_url or 'Default'}")
    print(f"   Server: {config.host}:{config.port}")
    print(f"   Models: BIG={config.big_model}, SMALL={config.small_model}")
    print(f"   Thinking: BIG_BUDGET={config.big_model_thinking_budget}, SMALL_BUDGET={config.small_model_thinking_budget}")
    cache_status = "✓" if config.enable_content_cache else "✗"
    print(f"   Cache: {cache_status} | Min chars: {config.cache_min_chars} | TTL: {config.cache_ttl_hours}h")
except Exception as e:
    print(f"❌ Configuration Error: {e}")
    sys.exit(1)
