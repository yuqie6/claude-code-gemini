import json
import uuid
from typing import Any, AsyncGenerator
from fastapi import HTTPException, Request

from src.models.claude import ClaudeMessagesResponse, ContentBlock, Usage, ClaudeMessagesRequest
from src.models.gemini import GeminiResponse
from src.core.constants import Constants

def convert_gemini_to_claude_response(response_dict: dict[str, Any], model: str, request_id: str) -> dict[str, Any]:
    """Converts a Gemini API response dictionary to a Claude-style dictionary."""

    # Debug: Print raw Gemini response for thinking analysis (handle bytes objects)
    try:
        print(f"🔍 Raw Gemini response: {json.dumps(response_dict, ensure_ascii=False, indent=2)}")
    except TypeError as e:
        print(f"🔍 Raw Gemini response (contains non-serializable objects): {str(response_dict)[:500]}...")
        print(f"🔍 JSON serialization error: {e}")

    gemini_response = GeminiResponse.model_validate(response_dict)
    
    content_blocks = []
    stop_reason = None
    
    if gemini_response.candidates:
        candidate = gemini_response.candidates[0]
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if part.text:
                    # Check if this is a thought summary - FIXED
                    is_thought = getattr(part, 'thought', False)
                    print(f"🔍 DEBUG: part.text exists, is_thought={is_thought}")

                    # Create text block with proper thinking format
                    if is_thought:
                        # Wrap thinking content in <thinking> tags like Claude
                        wrapped_text = f"<thinking>\n{part.text}\n</thinking>"
                        text_block = ContentBlock(type='text', text=wrapped_text)
                        print(f"🧠 Thought summary wrapped in <thinking> tags: {part.text[:100]}...")
                    else:
                        # Regular text content
                        text_block = ContentBlock(type='text', text=part.text)

                    content_blocks.append(text_block)
                elif part.function_call:
                    # Create tool use block with improved handling
                    tool_block = ContentBlock(
                        type='tool_use',
                        id=f"toolu_{str(uuid.uuid4())[:8]}",
                        name=part.function_call.name,
                        input=part.function_call.args or {}
                    )
                    content_blocks.append(tool_block)

                    # Log function call for debugging
                    print(f"🔧 Function call detected - Name: {part.function_call.name}, Args: {part.function_call.args}")

        if candidate.finish_reason:
            if candidate.finish_reason == 'STOP':
                stop_reason = 'end_turn'
            elif candidate.finish_reason == 'MAX_TOKENS':
                stop_reason = 'max_tokens'
            elif candidate.finish_reason == 'TOOL_CODE':
                stop_reason = 'tool_use'
            else:
                stop_reason = 'stop_sequence'

    usage_data = gemini_response.usage_metadata

    # Extract thinking tokens if present - DETAILED DEBUG
    print(f"🔍 DEBUG: usage_data type: {type(usage_data)}")
    print(f"🔍 DEBUG: usage_data content: {usage_data}")

    thoughts_tokens = 0  # Default to 0 instead of None
    if usage_data and hasattr(usage_data, 'thoughts_token_count'):
        raw_thoughts = getattr(usage_data, 'thoughts_token_count', 0)
        print(f"🔍 DEBUG: Raw thoughts_token_count: {raw_thoughts} (type: {type(raw_thoughts)})")
        thoughts_tokens = raw_thoughts or 0
        if thoughts_tokens > 0:
            print(f"🧠 Thinking tokens detected in non-streaming response: {thoughts_tokens}")
        else:
            print(f"🔍 DEBUG: No thinking tokens found (raw: {raw_thoughts}, processed: {thoughts_tokens})")
    else:
        print(f"🔍 DEBUG: No usage_data or no thoughts_token_count attribute")

    # Create usage object - always include thoughts_token_count if > 0
    usage_dict = {
        "input_tokens": usage_data.prompt_token_count if usage_data and usage_data.prompt_token_count else 0,
        "output_tokens": usage_data.candidates_token_count if usage_data and usage_data.candidates_token_count else 0
    }

    # Add thinking tokens if present
    if thoughts_tokens > 0:
        usage_dict["thoughts_token_count"] = thoughts_tokens
        print(f"🧠 Adding thoughts_token_count to response: {thoughts_tokens}")

    claude_usage = Usage(**usage_dict)

    claude_response = ClaudeMessagesResponse(
        id=request_id,
        type='message',
        role='assistant',
        model=model,
        content=content_blocks,
        stop_reason=stop_reason,
        usage=claude_usage
    )
    
    # Don't exclude None values for thinking-related fields
    response_dict = claude_response.model_dump(exclude_none=False)

    # Clean up None values except for thinking-related fields
    cleaned_response = {}
    for key, value in response_dict.items():
        if value is not None:
            cleaned_response[key] = value
        elif key in ['thoughts_token_count']:  # Keep thinking fields even if None
            cleaned_response[key] = value

    return cleaned_response

async def convert_gemini_to_claude_stream_response(gemini_stream: AsyncGenerator[dict[str, Any], None], model: str, request_id: str) -> AsyncGenerator[bytes, None]:
    """Converts a Gemini API stream to a Claude-style SSE stream with complete event sequence.

    This function implements a complete Claude-compatible SSE event sequence:
    1. message_start - Initialize the message with metadata
    2. content_block_start - Start content block (text or tool_use)
    3. ping - Keep connection alive
    4. content_block_delta - Stream content incrementally (text or function args)
    5. content_block_stop - End content block
    6. message_delta - Include final stop_reason and usage statistics
    7. message_stop - Complete the message

    Key Features:
    - Complete function call support in streaming mode
    - Thought signature support for thinking models
    - Accurate token counting with usage_metadata accumulation
    - Robust error handling with fallback mechanisms
    - Debug logging for troubleshooting

    Args:
        gemini_stream: Async generator yielding Gemini API response chunks
        model: Model name for the response
        request_id: Unique request identifier

    Yields:
        bytes: SSE-formatted events compatible with Claude API

    Note:
        This function resolves the critical issue where LLMs wouldn't call functions
        in streaming mode by properly handling function_call parts in the stream.
    """

    message_id = f"msg_{uuid.uuid4().hex[:24]}"

    # Send initial SSE events
    yield f"event: {Constants.EVENT_MESSAGE_START}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_START, 'message': {'id': message_id, 'type': 'message', 'role': Constants.ROLE_ASSISTANT, 'model': model, 'content': [], 'stop_reason': None, 'stop_sequence': None, 'usage': {'input_tokens': 0, 'output_tokens': 0}}}, ensure_ascii=False)}\n\n".encode('utf-8')

    yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_START, 'index': 0, 'content_block': {'type': Constants.CONTENT_TEXT, 'text': ''}}, ensure_ascii=False)}\n\n".encode('utf-8')

    yield f"event: {Constants.EVENT_PING}\ndata: {json.dumps({'type': Constants.EVENT_PING}, ensure_ascii=False)}\n\n".encode('utf-8')

    # Initialize tracking variables
    content_block_index = 0  # Global index for all content blocks (text and tools)
    final_stop_reason = Constants.STOP_END_TURN
    usage_data = {"input_tokens": 0, "output_tokens": 0, "thoughts_token_count": 0}
    chunk_count = 0  # For periodic ping events
    last_token_input = 0  # Track token changes to avoid duplicate logs
    last_token_output = 0
    last_thoughts_tokens = 0

    # Thinking content accumulation
    thinking_buffer = ""
    thinking_active = False
    thinking_sent = False  # Track thinking token changes

    try:
        async for chunk_dict in gemini_stream:
            chunk_count += 1

            # Only log chunk details every 20 chunks or if it contains important info (function calls)
            has_function_call = bool(chunk_dict.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("function_call"))
            if chunk_count % 20 == 0 or has_function_call:
                print(f"🔍 Processing Gemini chunk #{chunk_count}" + (" (function call detected)" if has_function_call else " (progress update)"))

            # Send periodic ping to keep connection alive
            if chunk_count % 5 == 0:  # Every 5 chunks
                yield f"event: {Constants.EVENT_PING}\ndata: {json.dumps({'type': Constants.EVENT_PING}, ensure_ascii=False)}\n\n".encode('utf-8')

            # Handle error responses
            if chunk_dict.get("type") == "error":
                error_event = {
                    "type": "error",
                    "error": chunk_dict.get("error", {"type": "api_error", "message": "Gemini API error"}),
                }
                yield f"event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n".encode('utf-8')
                return

            # Extract candidates from chunk
            candidates = chunk_dict.get("candidates", [])
            if not candidates:
                continue

            candidate = candidates[0]

            # Handle content (text and function calls) - support parallel function calls
            content = candidate.get("content", {})
            if content:
                parts = content.get("parts", [])
                for part in parts:
                    # Handle text content (both regular text and thought summaries)
                    if part.get("text"):
                        text = part["text"]

                        # Check if this is a thought summary
                        is_thought = part.get("thought", False)

                        # Handle thinking content with buffering
                        if is_thought:
                            # Accumulate thinking content
                            thinking_buffer += text
                            thinking_active = True
                            print(f"🧠 Accumulating thought content: {text[:50]}...")
                            # Skip sending this chunk, but don't skip the rest of the loop
                            text_to_send = ""
                        else:
                            # If we have accumulated thinking content, send it first
                            if thinking_active and thinking_buffer and not thinking_sent:
                                # Send complete thinking content wrapped in tags
                                thinking_text = f"<thinking>\n{thinking_buffer}\n</thinking>"
                                thinking_delta = {
                                    'type': Constants.EVENT_CONTENT_BLOCK_DELTA,
                                    'index': 0,  # Use index 0 for the main text content block
                                    'delta': {'type': Constants.DELTA_TEXT, 'text': thinking_text}
                                }
                                yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps(thinking_delta, ensure_ascii=False)}\n\n".encode('utf-8')
                                print(f"🧠 Sent complete thinking content: {len(thinking_buffer)} chars")
                                thinking_sent = True

                            # Send regular content
                            text_to_send = text

                        # CRITICAL FIX: Send each character immediately for true streaming
                        # This ensures real-time character-by-character display like Claude native API
                        if text_to_send:  # Only process if text is not empty
                            delta_data = {
                                'type': Constants.EVENT_CONTENT_BLOCK_DELTA,
                                'index': content_block_index,
                                'delta': {'type': Constants.DELTA_TEXT, 'text': text_to_send}
                            }

                            # Include thought signature if present (for thinking models)
                            if part.get("thought_signature"):
                                delta_data["thought_signature"] = part["thought_signature"]
                                print(f"🧠 Thought signature included in text delta")

                            # Send immediately without buffering
                            sse_event = f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps(delta_data, ensure_ascii=False)}\n\n".encode('utf-8')
                            yield sse_event

                            # Debug log for very small chunks (only log first few to avoid spam)
                            if chunk_count <= 5 or len(text_to_send) > 10:
                                print(f"📤 Sent text delta #{chunk_count}: '{text_to_send}' (length: {len(text_to_send)})")

                    # Handle function calls - support parallel function calls with proper indexing
                    elif part.get("function_call"):
                        function_call = part["function_call"]
                        tool_use_id = f"toolu_{uuid.uuid4().hex[:8]}"

                        # Increment index for each new content block (parallel function calls)
                        content_block_index += 1
                        current_tool_index = content_block_index

                        # Send tool use content block start
                        tool_block_data = {
                            "type": Constants.EVENT_CONTENT_BLOCK_START,
                            "index": current_tool_index,
                            "content_block": {
                                "type": Constants.CONTENT_TOOL_USE,
                                "id": tool_use_id,
                                "name": function_call.get("name", ""),
                                "input": {}
                            }
                        }

                        # Include thought signature if present (for thinking models)
                        if part.get("thought_signature"):
                            tool_block_data["thought_signature"] = part["thought_signature"]
                            print(f"🧠 Thought signature included in function call")

                        yield f"event: {Constants.EVENT_CONTENT_BLOCK_START}\ndata: {json.dumps(tool_block_data, ensure_ascii=False)}\n\n".encode('utf-8')

                        # Send tool use input delta - handle args properly
                        function_args = function_call.get("args", {})
                        if function_args:
                            # Send the complete input as partial_json (Gemini provides complete args)
                            input_delta_data = {
                                "type": Constants.EVENT_CONTENT_BLOCK_DELTA,
                                "index": current_tool_index,
                                "delta": {
                                    "type": Constants.DELTA_INPUT_JSON,
                                    "partial_json": json.dumps(function_args)
                                }
                            }
                            yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps(input_delta_data, ensure_ascii=False)}\n\n".encode('utf-8')

                        # Send tool use content block stop
                        tool_stop_data = {
                            "type": Constants.EVENT_CONTENT_BLOCK_STOP,
                            "index": current_tool_index
                        }
                        yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps(tool_stop_data, ensure_ascii=False)}\n\n".encode('utf-8')

                        # Update final stop reason for tool use
                        final_stop_reason = Constants.STOP_TOOL_USE

                        # Log parallel function call for debugging
                        print(f"🔧 Parallel function call - Index: {current_tool_index}, Name: {function_call.get('name', '')}")

            # Handle finish reason
            finish_reason = candidate.get("finish_reason")
            if finish_reason:
                if finish_reason == "MAX_TOKENS":
                    final_stop_reason = Constants.STOP_MAX_TOKENS
                elif finish_reason == "TOOL_CODE":
                    final_stop_reason = Constants.STOP_TOOL_USE
                elif finish_reason == "STOP":
                    final_stop_reason = Constants.STOP_END_TURN
                else:
                    final_stop_reason = Constants.STOP_END_TURN

            # Accumulate usage metadata - Gemini provides cumulative counts in streaming
            usage_metadata = chunk_dict.get("usage_metadata")
            if usage_metadata:
                # According to Gemini API docs, usage_metadata contains cumulative token counts
                # prompt_token_count: total input tokens (cumulative)
                # candidates_token_count: total output tokens so far (cumulative)
                # thoughts_token_count: total thinking tokens so far (cumulative)
                if usage_metadata.get("prompt_token_count") is not None:
                    usage_data["input_tokens"] = usage_metadata["prompt_token_count"]
                if usage_metadata.get("candidates_token_count") is not None:
                    usage_data["output_tokens"] = usage_metadata["candidates_token_count"]
                if usage_metadata.get("thoughts_token_count") is not None:
                    usage_data["thoughts_token_count"] = usage_metadata["thoughts_token_count"]

                # Only log token updates when they change to avoid spam
                if (usage_data["input_tokens"] != last_token_input or
                    usage_data["output_tokens"] != last_token_output or
                    usage_data["thoughts_token_count"] != last_thoughts_tokens):

                    # Log thinking tokens separately if present
                    if usage_data["thoughts_token_count"] > 0:
                        print(f"🔢 Token update - Input: {usage_data['input_tokens']}, Output: {usage_data['output_tokens']}, Thinking: {usage_data['thoughts_token_count']}")
                    else:
                        print(f"🔢 Token update - Input: {usage_data['input_tokens']}, Output: {usage_data['output_tokens']}")

                    last_token_input = usage_data["input_tokens"]
                    last_token_output = usage_data["output_tokens"]
                    last_thoughts_tokens = usage_data["thoughts_token_count"]

    except Exception as e:
        # Handle streaming errors gracefully
        error_event = {
            "type": "error",
            "error": {"type": "api_error", "message": f"Gemini streaming error: {str(e)}"},
        }
        yield f"event: error\ndata: {json.dumps(error_event, ensure_ascii=False)}\n\n".encode('utf-8')
        return

    # Handle any remaining thinking content
    if thinking_active and thinking_buffer and not thinking_sent:
        # Send complete thinking content wrapped in tags
        thinking_text = f"<thinking>\n{thinking_buffer}\n</thinking>"
        thinking_delta = {
            'type': Constants.EVENT_CONTENT_BLOCK_DELTA,
            'index': 0,  # Use index 0 for the main text content block
            'delta': {'type': Constants.DELTA_TEXT, 'text': thinking_text}
        }
        yield f"event: {Constants.EVENT_CONTENT_BLOCK_DELTA}\ndata: {json.dumps(thinking_delta, ensure_ascii=False)}\n\n".encode('utf-8')
        print(f"🧠 Sent final thinking content: {len(thinking_buffer)} chars")

    # Send final SSE events with final token statistics
    if usage_data.get('thoughts_token_count', 0) > 0:
        print(f"📊 Final token statistics - Input: {usage_data['input_tokens']}, Output: {usage_data['output_tokens']}, Thinking: {usage_data['thoughts_token_count']}")
    else:
        print(f"📊 Final token statistics - Input: {usage_data['input_tokens']}, Output: {usage_data['output_tokens']}")

    # Send content block stop for the initial text block (index 0)
    yield f"event: {Constants.EVENT_CONTENT_BLOCK_STOP}\ndata: {json.dumps({'type': Constants.EVENT_CONTENT_BLOCK_STOP, 'index': 0}, ensure_ascii=False)}\n\n".encode('utf-8')

    yield f"event: {Constants.EVENT_MESSAGE_DELTA}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_DELTA, 'delta': {'stop_reason': final_stop_reason, 'stop_sequence': None}, 'usage': usage_data}, ensure_ascii=False)}\n\n".encode('utf-8')

    yield f"event: {Constants.EVENT_MESSAGE_STOP}\ndata: {json.dumps({'type': Constants.EVENT_MESSAGE_STOP}, ensure_ascii=False)}\n\n".encode('utf-8')

    # Signal end of stream - this is crucial for client to recognize conversation end
    yield b"data: [DONE]\n\n"

    # Final debug log
    print(f"🏁 Gemini stream completed - Total chunks processed: {chunk_count}")
    