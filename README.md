# Claude to Gemini Proxy

A proxy server that enables **Claude Code** and other Claude-compatible tools to work with **Google Gemini API**. Convert Claude API requests to Gemini API calls, allowing you to use Google's powerful Gemini models through the familiar Claude API interface.

![Claude Code Proxy](demo.png)

## Features

- **Full Claude API Compatibility**: Complete `/v1/messages` endpoint support
- **Gemini API Integration**: Seamless conversion to Google Gemini API calls
- **Smart Model Mapping**: Configure BIG and SMALL Gemini models via environment variables
- **Function Calling**: Complete tool use support with proper schema conversion
- **Streaming Responses**: Real-time SSE streaming support with Gemini
- **Thinking Support**: Full support for Gemini 2.5 thinking capabilities with configurable budgets
- **Image Support**: Base64 encoded image input for multimodal interactions
- **Error Handling**: Comprehensive error handling and logging

## Quick Start

### 1. Install Dependencies

```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your API configuration
```

### 3. Start Server

```bash
# Direct run
python start_proxy.py

# Or with UV
uv run claude-code-proxy
```

### 4. Use with Claude Code

```bash
ANTHROPIC_BASE_URL=http://localhost:8082 ANTHROPIC_AUTH_TOKEN="some-api-key" claude
```

## Configuration

### Environment Variables

**Required:**

- `GEMINI_API_KEY` - Your Google Gemini API key ([Get it here](https://aistudio.google.com/app/apikey))

**Model Configuration:**

- `BIG_MODEL` - Model for Claude sonnet/opus requests (default: `gemini-2.5-pro`)
- `SMALL_MODEL` - Model for Claude haiku requests (default: `gemini-2.5-flash`)

**API Configuration:**

- `GEMINI_BASE_URL` - Gemini API base URL (default: `https://generativelanguage.googleapis.com`)

**Server Settings:**

- `HOST` - Server host (default: `0.0.0.0`)
- `PORT` - Server port (default: `8082`)
- `LOG_LEVEL` - Logging level (default: `INFO`)

**Performance:**

- `MAX_TOKENS_LIMIT` - Token limit (default: `4096`)
- `MIN_TOKENS_LIMIT` - Minimum token limit (default: `100`)
- `REQUEST_TIMEOUT` - Request timeout in seconds (default: `90`)
- `MAX_RETRIES` - Maximum retry attempts (default: `2`)

**Thinking (Gemini 2.5 Models):**

- `BIG_MODEL_THINKING_BUDGET` - Thinking budget for big models (Pro/Sonnet/Opus) (default: `-1` for dynamic thinking)
- `SMALL_MODEL_THINKING_BUDGET` - Thinking budget for small models (Flash/Haiku) (default: `10000`)
- `ENABLE_THINKING_BY_DEFAULT` - Enable thinking by default (default: `true`)

### Model Mapping

The proxy maps Claude model requests to your configured Gemini models:

| Claude Request                 | Mapped To     | Environment Variable        |
| ------------------------------ | ------------- | --------------------------- |
| Models with "haiku"            | `SMALL_MODEL` | Default: `gemini-2.5-flash` |
| Models with "sonnet" or "opus" | `BIG_MODEL`   | Default: `gemini-2.5-pro`   |

### Gemini Configuration Examples

#### Standard Gemini API

```bash
GEMINI_API_KEY="your-gemini-api-key"
# GEMINI_BASE_URL="https://generativelanguage.googleapis.com"  # Default
BIG_MODEL="gemini-2.5-pro"
SMALL_MODEL="gemini-2.5-flash"
```

#### Gemini 1.5 Models

```bash
GEMINI_API_KEY="your-gemini-api-key"
BIG_MODEL="gemini-1.5-pro-latest"
SMALL_MODEL="gemini-1.5-flash-latest"
```

#### Custom Gemini Endpoint

```bash
GEMINI_API_KEY="your-gemini-api-key"
GEMINI_BASE_URL="https://your-custom-gemini-proxy.com/gemini"
BIG_MODEL="gemini-2.5-pro"
SMALL_MODEL="gemini-2.5-flash"
```

#### Thinking Configuration

```bash
# Enable thinking with custom budgets
BIG_MODEL_THINKING_BUDGET="-1"      # Dynamic thinking for Pro models
SMALL_MODEL_THINKING_BUDGET="10000" # Fixed budget for Flash models
ENABLE_THINKING_BY_DEFAULT="true"
```

### Getting Your Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key to your `.env` file

## Usage Examples

### Basic Chat

```python
import httpx

response = httpx.post(
    "http://localhost:8082/v1/messages",
    json={
        "model": "claude-3-5-sonnet-20241022",  # Maps to gemini-2.5-pro
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "Hello! How are you?"}
        ]
    }
)
```

### Streaming Response

```python
import httpx

with httpx.stream(
    "POST",
    "http://localhost:8082/v1/messages",
    json={
        "model": "claude-3-haiku-20240307",  # Maps to gemini-2.5-flash
        "max_tokens": 100,
        "stream": True,
        "messages": [
            {"role": "user", "content": "Tell me a story"}
        ]
    }
) as response:
    for line in response.iter_lines():
        if line.startswith("data: "):
            print(line[6:])

### Function Calling

```python
response = httpx.post(
    "http://localhost:8082/v1/messages",
    json={
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "messages": [
            {"role": "user", "content": "What's the weather like?"}
        ],
        "tools": [
            {
                "name": "get_weather",
                "description": "Get current weather information",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"}
                    },
                    "required": ["location"]
                }
            }
        ]
    }
)
```

### Thinking Mode (Gemini 2.5)

```python
response = httpx.post(
    "http://localhost:8082/v1/messages",
    json={
        "model": "claude-3-5-sonnet-20241022",
        "max_tokens": 100,
        "thinking": {
            "enabled": True,
            "budget": -1  # Dynamic thinking
        },
        "messages": [
            {"role": "user", "content": "Solve this complex math problem: ..."}
        ]
    }
)
```

## Integration with Claude Code

This proxy is designed to work seamlessly with Claude Code CLI:

```bash
# Start the proxy
python start_proxy.py

# Use Claude Code with the proxy
ANTHROPIC_BASE_URL=http://localhost:8082 claude

# Or set permanently
export ANTHROPIC_BASE_URL=http://localhost:8082
claude
```

## Testing

Test the proxy functionality:

```bash
# Run comprehensive tests
python src/test_claude_to_openai.py
```

## Development

### Using UV

```bash
# Install dependencies
uv sync

# Run server
uv run claude-code-proxy

# Format code
uv run black src/
uv run isort src/

# Type checking
uv run mypy src/
```

### Project Structure

```
claude-code-proxy/
├── src/
│   ├── main.py  # Main server
│   ├── test_claude_to_openai.py    # Tests
│   └── [other modules...]
├── start_proxy.py                  # Startup script
├── .env.example                    # Config template
└── README.md                       # This file
```

## Performance

- **Async/await** for high concurrency
- **Connection pooling** for efficiency
- **Streaming support** for real-time responses
- **Configurable timeouts** and retries
- **Smart error handling** with detailed logging

## License

MIT License
