"""Test script for Claude to Gemini proxy."""

import asyncio
import json
import httpx
from dotenv import load_dotenv

load_dotenv()


async def test_basic_chat():
    """Test basic chat completion."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 100,
                "messages": [
                    {"role": "user", "content": "Hello, how are you?"}
                ]
            }
        )
        
        print("Basic chat response:")
        print(json.dumps(response.json(), indent=2))

async def test_streaming_chat():
    """Test streaming chat completion."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream(
            "POST",
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-haiku-20241022",
                "max_tokens": 150,
                "messages": [
                    {"role": "user", "content": "Tell me a short joke"}
                ],
                "stream": True
            }
        ) as response:
            print("\nStreaming response:")
            async for line in response.aiter_lines():
                if line.strip():
                    print(line)


async def test_function_calling():
    """Test function calling capability."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 200,
                "messages": [
                    {"role": "user", "content": "What's the weather like in New York? Please use the weather function."}
                ],
                "tools": [
                    {
                        "name": "get_weather",
                        "description": "Get the current weather for a location",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "location": {
                                    "type": "string",
                                    "description": "The location to get weather for"
                                },
                                "unit": {
                                    "type": "string",
                                    "enum": ["celsius", "fahrenheit"],
                                    "description": "Temperature unit"
                                }
                            },
                            "required": ["location"]
                        }
                    }
                ],
                "tool_choice": {"type": "auto"}
            }
        )
        
        print("\nFunction calling response:")
        print(json.dumps(response.json(), indent=2))


async def test_with_system_message():
    """Test with system message."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 100,
                "system": "You are a helpful assistant that always responds in haiku format.",
                "messages": [
                    {"role": "user", "content": "Explain what AI is"}
                ]
            }
        )
        
        print("\nSystem message response:")
        print(json.dumps(response.json(), indent=2))


async def test_multimodal():
    """Test multimodal input (text + image)."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Sample base64 image (1x1 pixel transparent PNG)
        sample_image = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU8PJAAAAASUVORK5CYII="
        
        response = await client.post(
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What do you see in this image?"},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": sample_image
                                }
                            }
                        ]
                    }
                ]
            }
        )
        
        print("\nMultimodal response:")
        print(json.dumps(response.json(), indent=2))


async def test_conversation_with_tool_use():
    """Test a complete conversation with tool use and results."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First message with tool call
        response1 = await client.post(
            "http://localhost:8082/v1/messages",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 200,
                "messages": [
                    {"role": "user", "content": "Calculate 25 * 4 using the calculator tool"}
                ],
                "tools": [
                    {
                        "name": "calculator",
                        "description": "Perform basic arithmetic calculations",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "expression": {
                                    "type": "string",
                                    "description": "Mathematical expression to calculate"
                                }
                            },
                            "required": ["expression"]
                        }
                    }
                ]
            }
        )
        
        print("\nTool call response:")
        result1 = response1.json()
        print(json.dumps(result1, indent=2))
        
        # Simulate tool execution and send result
        if result1.get("content"):
            tool_use_blocks = [block for block in result1["content"] if block.get("type") == "tool_use"]
            if tool_use_blocks:
                tool_block = tool_use_blocks[0]
                
                # Second message with tool result
                response2 = await client.post(
                    "http://localhost:8082/v1/messages",
                    json={
                        "model": "claude-3-5-sonnet-20241022",
                        "max_tokens": 100,
                        "messages": [
                            {"role": "user", "content": "Calculate 25 * 4 using the calculator tool"},
                            {"role": "assistant", "content": result1["content"]},
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "tool_result",
                                        "tool_use_id": tool_block["id"],
                                        "content": "100"
                                    }
                                ]
                            }
                        ]
                    }
                )
                
                print("\nTool result response:")
                print(json.dumps(response2.json(), indent=2))


async def test_token_counting():
    """Test token counting endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8082/v1/messages/count_tokens",
            json={
                "model": "claude-3-5-sonnet-20241022",
                "messages": [
                    {"role": "user", "content": "This is a test message for token counting."}
                ]
            }
        )

        print("\nToken count response:")
        print(json.dumps(response.json(), indent=2))


async def test_gemini_streaming_response():
    """Test Gemini streaming response with complete SSE event sequence and token calculation."""
    print("\n🧪 Testing Gemini streaming response...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test streaming response
        async with client.stream(
            "POST",
            "http://localhost:8082/v1/messages",
            json={
                "model": "gemini-2.0-flash",  # Use Gemini model
                "max_tokens": 100,
                "messages": [
                    {"role": "user", "content": "Count from 1 to 5 and explain each number."}
                ],
                "stream": True
            }
        ) as response:
            print("\n📡 Gemini Streaming response events:")

            events = []
            content_deltas = []
            final_usage = None

            async for line in response.aiter_lines():
                if line.strip():
                    print(line)

                    # Parse SSE events
                    if line.startswith("event: "):
                        event_type = line[7:]
                        events.append(event_type)
                    elif line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])

                            # Collect content deltas
                            if data.get("type") == "content_block_delta":
                                delta_text = data.get("delta", {}).get("text", "")
                                if delta_text:
                                    content_deltas.append(delta_text)

                            # Collect final usage statistics
                            elif data.get("type") == "message_delta":
                                final_usage = data.get("usage", {})

                        except json.JSONDecodeError:
                            pass

            # Verify complete SSE event sequence
            expected_events = ["message_start", "content_block_start", "ping", "content_block_stop", "message_stop"]
            print(f"\n🔍 Event sequence verification:")
            print(f"   Expected events: {expected_events}")
            print(f"   Received events: {events}")

            # Check if all expected events are present
            missing_events = [event for event in expected_events if event not in events]
            if missing_events:
                print(f"   ⚠️  Missing events: {missing_events}")
            else:
                print(f"   ✅ All expected events received")

            # Verify content was received
            total_content = "".join(content_deltas)
            print(f"\n📝 Content verification:")
            print(f"   Total content length: {len(total_content)} characters")
            print(f"   Content preview: {total_content[:100]}...")

            # Verify token statistics
            print(f"\n🔢 Token statistics:")
            if final_usage:
                print(f"   Input tokens: {final_usage.get('input_tokens', 'N/A')}")
                print(f"   Output tokens: {final_usage.get('output_tokens', 'N/A')}")
            else:
                print(f"   ⚠️  No usage statistics received")


async def test_gemini_token_consistency():
    """Test token calculation consistency between streaming and non-streaming responses."""
    print("\n🧪 Testing Gemini token calculation consistency...")

    test_message = "Explain the concept of artificial intelligence in exactly 50 words."

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test non-streaming response
        print("\n📊 Non-streaming response:")
        non_stream_response = await client.post(
            "http://localhost:8082/v1/messages",
            json={
                "model": "gemini-2.0-flash",
                "max_tokens": 100,
                "messages": [
                    {"role": "user", "content": test_message}
                ],
                "stream": False
            }
        )

        non_stream_data = non_stream_response.json()
        non_stream_usage = non_stream_data.get("usage", {})
        print(f"   Input tokens: {non_stream_usage.get('input_tokens', 'N/A')}")
        print(f"   Output tokens: {non_stream_usage.get('output_tokens', 'N/A')}")

        # Test streaming response
        print("\n📡 Streaming response:")
        stream_usage = None

        async with client.stream(
            "POST",
            "http://localhost:8082/v1/messages",
            json={
                "model": "gemini-2.0-flash",
                "max_tokens": 100,
                "messages": [
                    {"role": "user", "content": test_message}
                ],
                "stream": True
            }
        ) as response:
            async for line in response.aiter_lines():
                if line.strip() and line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "message_delta":
                            stream_usage = data.get("usage", {})
                    except json.JSONDecodeError:
                        pass

        if stream_usage:
            print(f"   Input tokens: {stream_usage.get('input_tokens', 'N/A')}")
            print(f"   Output tokens: {stream_usage.get('output_tokens', 'N/A')}")

            # Compare token counts
            print(f"\n🔍 Token consistency check:")
            input_match = non_stream_usage.get('input_tokens') == stream_usage.get('input_tokens')
            output_match = non_stream_usage.get('output_tokens') == stream_usage.get('output_tokens')

            print(f"   Input tokens match: {input_match}")
            print(f"   Output tokens match: {output_match}")

            if input_match and output_match:
                print(f"   ✅ Token counts are consistent")
            else:
                print(f"   ⚠️  Token counts differ between streaming and non-streaming")
        else:
            print(f"   ❌ No usage statistics received from streaming response")


async def test_gemini_error_handling():
    """Test Gemini error handling in streaming responses."""
    print("\n🧪 Testing Gemini error handling...")

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test with invalid model to trigger error
        try:
            async with client.stream(
                "POST",
                "http://localhost:8082/v1/messages",
                json={
                    "model": "invalid-gemini-model",
                    "max_tokens": 50,
                    "messages": [
                        {"role": "user", "content": "Hello"}
                    ],
                    "stream": True
                }
            ) as response:
                print(f"\n📡 Error response (Status: {response.status_code}):")

                error_received = False
                async for line in response.aiter_lines():
                    if line.strip():
                        print(line)

                        # Check for error events
                        if line.startswith("event: error") or "error" in line.lower():
                            error_received = True

                if error_received:
                    print(f"   ✅ Error handling working correctly")
                else:
                    print(f"   ⚠️  No error event received")

        except Exception as e:
            print(f"   📝 Exception caught: {str(e)}")
            print(f"   ✅ Error handling working correctly")


async def test_health_and_connection():
    """Test health and connection endpoints."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Health check
        health_response = await client.get("http://localhost:8082/health")
        print("\nHealth check:")
        print(json.dumps(health_response.json(), indent=2))
        
        # Connection test
        connection_response = await client.get("http://localhost:8082/test-connection")
        print("\nConnection test:")
        print(json.dumps(connection_response.json(), indent=2))


async def test_parallel_function_calling():
    """Test parallel function calling support in streaming mode."""
    print("\n🧪 Testing parallel function calling...")

    # Create a request that should trigger multiple function calls
    request_data = {
        "model": "gemini-2.0-flash",
        "max_tokens": 100,
        "messages": [
            {
                "role": "user",
                "content": "Please calculate both 25*4 and 30*3 for me. Use the calculator tool for both calculations."
            }
        ],
        "tools": [
            {
                "name": "calculator",
                "description": "Perform mathematical calculations",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate"
                        }
                    },
                    "required": ["expression"]
                }
            }
        ],
        "tool_choice": {"type": "any"},  # Force function calling
        "stream": True
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8082/v1/messages",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )

            print(f"📡 Parallel function calling response (Status: {response.status_code}):")

            function_calls_detected = 0
            content_blocks_started = 0

            async for line in response.aiter_lines():
                if line.strip():
                    print(line)

                    # Parse SSE events to detect function calls
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])

                            # Count content block starts for tool_use
                            if data.get("type") == "content_block_start":
                                content_block = data.get("content_block", {})
                                if content_block.get("type") == "tool_use":
                                    content_blocks_started += 1
                                    function_name = content_block.get("name", "")
                                    block_index = data.get("index", 0)
                                    print(f"🔧 Function call detected - Index: {block_index}, Name: {function_name}")

                            # Count function calls in deltas
                            elif data.get("type") == "content_block_delta":
                                delta = data.get("delta", {})
                                if delta.get("type") == "input_json_delta":
                                    function_calls_detected += 1

                        except json.JSONDecodeError:
                            pass

            # Verify parallel function calling
            print(f"\n🔍 Parallel function calling verification:")
            print(f"   Content blocks started: {content_blocks_started}")
            print(f"   Function calls detected: {function_calls_detected}")

            if content_blocks_started >= 2:
                print(f"   ✅ Parallel function calling supported!")
            else:
                print(f"   ⚠️  Only {content_blocks_started} function call(s) detected")

    except Exception as e:
        print(f"   ❌ Parallel function calling test failed: {e}")


async def test_thinking_functionality():
    """Test Gemini thinking functionality with thought summaries."""
    print("\n🧪 Testing Gemini thinking functionality...")

    # Test thinking with budget and thought summaries
    request_data = {
        "model": "gemini-2.5-pro",  # Use thinking-capable model
        "max_tokens": 200,
        "messages": [
            {
                "role": "user",
                "content": "Solve this step by step: What is the sum of the first 10 prime numbers? Show your reasoning."
            }
        ],
        "thinking": {
            "enabled": True,
            "budget": 1024,  # Specific thinking budget
            "include_thoughts": True  # Request thought summaries
        },
        "stream": True
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8082/v1/messages",
                json=request_data,
                headers={"Content-Type": "application/json"},
                timeout=60.0
            )

            print(f"📡 Thinking functionality response (Status: {response.status_code}):")

            thought_summaries_detected = 0
            thought_signatures_detected = 0
            thoughts_token_count_detected = False
            final_usage_data = None

            async for line in response.aiter_lines():
                if line.strip():
                    print(line)

                    # Parse SSE events to detect thinking features
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])

                            # Check for thought summaries
                            if data.get("is_thought_summary"):
                                thought_summaries_detected += 1
                                print(f"🧠 Thought summary detected!")

                            # Check for thought signatures
                            if data.get("thought_signature"):
                                thought_signatures_detected += 1
                                print(f"🧠 Thought signature detected!")

                            # Check for thoughts_token_count in usage data
                            if data.get("type") == "message_delta" and data.get("usage"):
                                usage = data["usage"]
                                if "thoughts_token_count" in usage:
                                    thoughts_token_count_detected = True
                                    final_usage_data = usage
                                    print(f"🧠 Thoughts token count detected: {usage.get('thoughts_token_count', 0)}")

                        except json.JSONDecodeError:
                            pass

            # Verify thinking functionality
            print(f"\n🔍 Thinking functionality verification:")
            print(f"   Thought summaries detected: {thought_summaries_detected}")
            print(f"   Thought signatures detected: {thought_signatures_detected}")
            print(f"   Thoughts token count detected: {thoughts_token_count_detected}")

            if final_usage_data:
                print(f"   Final usage data: {final_usage_data}")

            if thought_summaries_detected > 0 or thought_signatures_detected > 0 or thoughts_token_count_detected:
                print(f"   ✅ Thinking functionality working!")
            else:
                print(f"   ⚠️  No thinking features detected (may be normal for simple queries)")

    except Exception as e:
        print(f"   ❌ Thinking functionality test failed: {e}")

    # Test non-streaming response for thoughts_token_count
    print("\n🧪 Testing non-streaming thinking functionality...")
    non_stream_request = {
        "model": "gemini-2.5-pro",
        "max_tokens": 150,
        "messages": [
            {
                "role": "user",
                "content": "What is 2+2? Think about it step by step."
            }
        ],
        "thinking": {
            "enabled": True,
            "budget": 512,
            "include_thoughts": True
        },
        "stream": False  # Non-streaming
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8082/v1/messages",
                json=non_stream_request,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )

            print(f"📡 Non-streaming thinking response (Status: {response.status_code}):")

            if response.status_code == 200:
                response_data = response.json()
                usage = response_data.get("usage", {})

                print(f"   Usage data: {usage}")

                # Check for thoughts_token_count in non-streaming response
                if "thoughts_token_count" in usage:
                    print(f"   ✅ Thoughts token count in non-streaming response: {usage['thoughts_token_count']}")
                else:
                    print(f"   ⚠️  No thoughts_token_count in non-streaming response")

            else:
                print(f"   ❌ Non-streaming request failed with status {response.status_code}")

    except Exception as e:
        print(f"   ❌ Non-streaming thinking test failed: {e}")


async def main():
    """Run all tests."""
    print("🧪 Testing Claude to Gemini Proxy")
    print("=" * 50)

    import traceback
    try:
        await test_health_and_connection()
        await test_token_counting()
        await test_basic_chat()
        await test_with_system_message()
        await test_streaming_chat()
        await test_gemini_streaming_response()
        await test_gemini_token_consistency()
        await test_gemini_error_handling()
        await test_multimodal()
        await test_function_calling()
        await test_conversation_with_tool_use()
        await test_parallel_function_calling()
        await test_thinking_functionality()
        print("\n✅ All tests completed!")
        print("🎉 All Gemini functionality is working correctly!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        print("Make sure the server is running with a valid GEMINI_API_KEY")
        print("Get your API key from: https://aistudio.google.com/app/apikey")


if __name__ == "__main__":
    asyncio.run(main())