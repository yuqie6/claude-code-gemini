from fastapi import FastAPI
from src.api.endpoints import router as api_router
import uvicorn
import sys
from src.core.config import config

# Project now only supports Gemini API
app_title = "Claude-to-Gemini API Proxy"

app = FastAPI(title=app_title, version="1.0.0")

app.include_router(api_router)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(f"{app_title} v1.0.0")
        print("")
        print("Usage: python src/main.py")
        print("")
        print("Required environment variables:")
        print("  GEMINI_API_KEY - Your Google Gemini API key")
        print("                   Get it from: https://aistudio.google.com/app/apikey")
        print("")
        print("Optional environment variables:")
        print("  GEMINI_BASE_URL - Custom Gemini API endpoint")
        print("                    (default: https://generativelanguage.googleapis.com)")
        print(f"  BIG_MODEL - Model for sonnet/opus requests (default: gemini-2.5-pro)")
        print(f"  SMALL_MODEL - Model for haiku requests (default: gemini-2.5-flash)")
        print(f"  HOST - Server host (default: 0.0.0.0)")
        print(f"  PORT - Server port (default: 8082)")
        print(f"  LOG_LEVEL - Logging level (default: INFO)")
        print(f"  MAX_TOKENS_LIMIT - Token limit (default: 4096)")
        print(f"  MIN_TOKENS_LIMIT - Minimum token limit (default: 100)")
        print(f"  REQUEST_TIMEOUT - Request timeout in seconds (default: 90)")
        print("")
        print("Thinking configuration (Gemini 2.5 models):")
        print(f"  BIG_MODEL_THINKING_BUDGET - Thinking budget for big models (default: -1)")
        print(f"  SMALL_MODEL_THINKING_BUDGET - Thinking budget for small models (default: 10000)")
        print(f"  ENABLE_THINKING_BY_DEFAULT - Enable thinking by default (default: true)")
        print("")
        print("Model mapping:")
        print(f"  Claude haiku models -> {config.small_model}")
        print(f"  Claude sonnet/opus models -> {config.big_model}")
        print("")
        print("Features:")
        print("  ✅ Claude API compatibility")
        print("  ✅ Gemini API integration")
        print("  ✅ Function calling support")
        print("  ✅ Streaming responses")
        print("  ✅ Thinking mode (Gemini 2.5)")
        print("  ✅ Multimodal support")
        sys.exit(0)

    # Configuration summary
    print(f"{app_title} v1.0.0")
    print(f"✅ Configuration loaded successfully")
    print(f"   Gemini Base URL: {config.gemini_base_url or 'Default'}")
    print(f"   Models: BIG={config.big_model}, SMALL={config.small_model}")
    print(f"   Thinking: BIG_BUDGET={config.big_model_thinking_budget}, SMALL_BUDGET={config.small_model_thinking_budget}")

    print(f"   Big Model (sonnet/opus): {config.big_model}")
    print(f"   Small Model (haiku): {config.small_model}")
    print(f"   Max Tokens Limit: {config.max_tokens_limit}")
    print(f"   Request Timeout: {config.request_timeout}s")
    print(f"   Server: {config.host}:{config.port}")

    # 显示API类型 - 项目现在专注于Gemini API
    if config.gemini_api_key:
        print(f"   API Type: Gemini (Claude-compatible)")
    else:
        print(f"   API Type: Gemini (⚠️  API key not configured)")

    print("")

    # Parse log level - extract just the first word to handle comments
    log_level = config.log_level.split()[0].lower()
    
    # Validate and set default if invalid
    valid_levels = ['debug', 'info', 'warning', 'error', 'critical']
    if log_level not in valid_levels:
        log_level = 'info'

    # Start server
    uvicorn.run(
        "src.main:app",
        host=config.host,
        port=config.port,
        log_level=log_level,
        reload=False,
    )


if __name__ == "__main__":
    main()
