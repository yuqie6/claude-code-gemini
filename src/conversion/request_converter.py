import json
import logging
from typing import Any
import copy

from src.core.config import config
from src.models.claude import ClaudeMessagesRequest
# Gemini models imported as needed in the conversion function

logger = logging.getLogger(__name__)

# OpenAI conversion functions removed - project now focuses on Gemini API only

def _enhance_tool_description(tool_name: str, original_description: str) -> str:
    """
    Enhance tool descriptions to encourage Gemini to use tools more actively.
    Adds motivational prefixes based on tool type to combat Gemini's "laziness".
    """
    if not original_description:
        original_description = f"Tool: {tool_name}"

    # Identify tool types and add appropriate motivational prefixes
    tool_name_lower = tool_name.lower()

    # Search and information gathering tools
    if any(keyword in tool_name_lower for keyword in ['search', 'fetch', 'web', 'find', 'lookup', 'query', 'get']):
        prefix = "🔍 CRITICAL SEARCH TOOL: You MUST use this tool when you need current information or to search for data. "
        return f"{prefix}{original_description}"

    # Task management and planning tools
    elif any(keyword in tool_name_lower for keyword in ['todo', 'task', 'plan', 'write', 'manage', 'track']):
        prefix = "📋 REQUIRED TASK TOOL: You are REQUIRED to use this tool for task planning and tracking. Use it frequently throughout the conversation. "
        return f"{prefix}{original_description}"

    # File and code operations
    elif any(keyword in tool_name_lower for keyword in ['file', 'read', 'write', 'edit', 'code', 'bash', 'run', 'execute']):
        prefix = "⚡ ESSENTIAL ACTION TOOL: This tool is essential for completing tasks effectively. Use it proactively when needed. "
        return f"{prefix}{original_description}"

    # Analysis and debugging tools
    elif any(keyword in tool_name_lower for keyword in ['analyze', 'debug', 'check', 'test', 'validate', 'inspect']):
        prefix = "🔧 IMPORTANT ANALYSIS TOOL: Use this tool to thoroughly analyze and understand the situation before proceeding. "
        return f"{prefix}{original_description}"

    # Default enhancement for other tools
    else:
        prefix = "🛠️ ACTIVE TOOL USE REQUIRED: You should actively use this tool when appropriate. "
        return f"{prefix}{original_description}"

def _enhance_system_prompt(original_prompt: str, has_tools: bool) -> str:
    """
    Enhance system prompt to encourage more active tool usage.
    Adds specific instructions to combat Gemini's tendency to be "lazy" with tools.
    """
    if not has_tools:
        return original_prompt

    # Tool usage enhancement instructions
    tool_enhancement = """

🚀 CRITICAL TOOL USAGE INSTRUCTIONS:
- You MUST be proactive and aggressive in using the available tools
- When you need information, ALWAYS search first - don't guess or assume
- For task management, you MUST use TodoWrite tools frequently throughout the conversation
- Use search tools extensively when you need current information or documentation
- Don't be "lazy" - if a tool can help, USE IT immediately
- Tool usage is not optional - it's required for effective task completion
- When in doubt, use a tool rather than making assumptions

REMEMBER: Active tool usage is essential for providing accurate and helpful responses."""

    return f"{original_prompt}{tool_enhancement}"

def _create_information_summary(original_schema, adapted_schema):
    """
    Create information summary of original and adapted schemas to ensure no information loss
    """
    def _extract_constraints(schema_obj, path=""):
        """Recursively extract all constraint information from schema"""
        constraints = []
        if isinstance(schema_obj, dict):
            for key, value in schema_obj.items():
                current_path = f"{path}.{key}" if path else key

                # Extract various constraint information
                if key in ['minimum', 'maximum', 'exclusiveMinimum', 'exclusiveMaximum']:
                    constraints.append(f"{current_path}: {key} = {value}")
                elif key == 'format':
                    constraints.append(f"{current_path}: format = {value}")
                elif key in ['pattern', 'multipleOf', 'const']:
                    constraints.append(f"{current_path}: {key} = {value}")
                elif key in ['minLength', 'maxLength', 'minItems', 'maxItems']:
                    constraints.append(f"{current_path}: {key} = {value}")
                elif key in ['enum']:
                    constraints.append(f"{current_path}: enum = {json.dumps(value, ensure_ascii=False)}")
                elif key in ['examples', 'default']:
                    constraints.append(f"{current_path}: {key} = {json.dumps(value, ensure_ascii=False)}")
                elif isinstance(value, dict):
                    constraints.extend(_extract_constraints(value, current_path))
                elif isinstance(value, list) and key in ['anyOf', 'oneOf', 'allOf']:
                    for i, item in enumerate(value):
                        constraints.extend(_extract_constraints(item, f"{current_path}[{i}]"))
        return constraints

    original_constraints = _extract_constraints(original_schema)
    adapted_constraints = _extract_constraints(adapted_schema)

    # Find lost constraints
    lost_constraints = [c for c in original_constraints if c not in adapted_constraints]

    if lost_constraints:
        return f"Original constraints preserved in description: {'; '.join(lost_constraints)}"
    return None

def _deep_clean_schema_formats(obj):
    """
    Deep clean all fields that may not be supported by Gemini, ensuring no omissions
    """
    if isinstance(obj, dict):
        cleaned = {}
        # List of fields not supported by Gemini
        unsupported_fields = {
            'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf', 'const',
            'contentEncoding', 'contentMediaType', 'examples', 'default',
            'readOnly', 'writeOnly', 'deprecated', '$schema', 'additionalProperties',
            'patternProperties', 'dependencies'
        }

        for key, value in obj.items():
            if key in unsupported_fields:
                # Skip unsupported fields
                continue
            elif key == 'format' and obj.get('type') and str(obj.get('type')).lower() == 'string':
                # Only keep Gemini-supported formats
                if value in ['enum', 'date-time']:
                    cleaned[key] = value
                # Skip other formats, don't add to cleaned
            else:
                cleaned[key] = _deep_clean_schema_formats(value)
        return cleaned
    elif isinstance(obj, list):
        return [_deep_clean_schema_formats(item) for item in obj]
    else:
        return obj

def _gemini_schema_adapter(schema):
    """
    Recursively adapt JSON Schema to meet Gemini API requirements
    - Remove unsupported formats (except enum and date-time)
    - Remove unsupported fields like $schema, additionalProperties
    - Maintain conversion quality by adding removed information to description
    """
    if not isinstance(schema, dict):
        return schema

    adapted_schema = copy.deepcopy(schema)
    unsupported_info = []

    # Handle format restrictions for string types
    schema_type = adapted_schema.get('type', '')
    if isinstance(schema_type, str) and schema_type.lower() == 'string':
        if 'format' in adapted_schema:
            format_value = adapted_schema['format']
            if format_value not in ['enum', 'date-time']:
                unsupported_info.append(f"format: {format_value}")
                del adapted_schema['format']
                # To maintain conversion quality, add more specific descriptions based on format type
                current_desc = adapted_schema.get('description', '')
                format_descriptions = {
                    'url': 'Expected: valid URL format (e.g., https://example.com)',
                    'uri': 'Expected: valid URI format',
                    'email': 'Expected: valid email format (e.g., user@example.com)',
                    'hostname': 'Expected: valid hostname format',
                    'ipv4': 'Expected: valid IPv4 address format (e.g., 192.168.1.1)',
                    'ipv6': 'Expected: valid IPv6 address format',
                    'uuid': 'Expected: valid UUID format (e.g., 123e4567-e89b-12d3-a456-426614174000)',
                    'date': 'Expected: valid date format (YYYY-MM-DD)',
                    'time': 'Expected: valid time format (HH:MM:SS)',
                    'regex': 'Expected: valid regular expression pattern',
                    'json-pointer': 'Expected: valid JSON pointer format',
                    'relative-json-pointer': 'Expected: valid relative JSON pointer format',
                    'binary': 'Expected: binary data format',
                    'byte': 'Expected: base64-encoded binary data',
                    'password': 'Expected: password string (will be handled securely)'
                }

                format_hint = format_descriptions.get(format_value, f'Expected: {format_value} format')
                if current_desc:
                    adapted_schema['description'] = f"{current_desc} | {format_hint}"
                else:
                    adapted_schema['description'] = format_hint

    # Remove fields not supported by Gemini
    unsupported_keys = [
        '$schema', 'additionalProperties', 'patternProperties', 'dependencies',
        'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf', 'const',
        'contentEncoding', 'contentMediaType', 'examples', 'default',
        'readOnly', 'writeOnly', 'deprecated'
    ]
    for key in unsupported_keys:
        if key in adapted_schema:
            # For numeric constraint fields, try to convert to supported fields
            if key == 'exclusiveMinimum' and isinstance(adapted_schema[key], (int, float)):
                # exclusiveMinimum: 5 converts to minimum: 6 (if integer)
                if isinstance(adapted_schema[key], int):
                    adapted_schema['minimum'] = adapted_schema[key] + 1
                    unsupported_info.append(f'exclusiveMinimum: {adapted_schema[key]} -> minimum: {adapted_schema[key] + 1}')
                else:
                    # For float values, use minimum directly
                    adapted_schema['minimum'] = adapted_schema[key]
                    unsupported_info.append(f'exclusiveMinimum: {adapted_schema[key]} -> minimum: {adapted_schema[key]}')
            elif key == 'exclusiveMaximum' and isinstance(adapted_schema[key], (int, float)):
                # exclusiveMaximum: 10 converts to maximum: 9 (if integer)
                if isinstance(adapted_schema[key], int):
                    adapted_schema['maximum'] = adapted_schema[key] - 1
                    unsupported_info.append(f'exclusiveMaximum: {adapted_schema[key]} -> maximum: {adapted_schema[key] - 1}')
                else:
                    # For float values, use maximum directly
                    adapted_schema['maximum'] = adapted_schema[key]
                    unsupported_info.append(f'exclusiveMaximum: {adapted_schema[key]} -> maximum: {adapted_schema[key]}')
            else:
                # Add detailed description information for other removed fields
                current_desc = adapted_schema.get('description', '')
                field_descriptions = {
                    'multipleOf': f'Value must be multiple of {adapted_schema[key]}',
                    'const': f'Value must be exactly: {json.dumps(adapted_schema[key], ensure_ascii=False)}',
                    'examples': f'Example values: {json.dumps(adapted_schema[key], ensure_ascii=False)}',
                    'default': f'Default value: {json.dumps(adapted_schema[key], ensure_ascii=False)}',
                    'readOnly': 'This field is read-only' if adapted_schema[key] else '',
                    'writeOnly': 'This field is write-only' if adapted_schema[key] else '',
                    'deprecated': 'This field is deprecated' if adapted_schema[key] else '',
                    'contentEncoding': f'Content encoding: {adapted_schema[key]}',
                    'contentMediaType': f'Content media type: {adapted_schema[key]}',
                    'additionalProperties': f'Additional properties: {json.dumps(adapted_schema[key], ensure_ascii=False)}',
                    'patternProperties': f'Pattern properties: {json.dumps(adapted_schema[key], ensure_ascii=False)}',
                    'dependencies': f'Dependencies: {json.dumps(adapted_schema[key], ensure_ascii=False)}'
                }

                field_hint = field_descriptions.get(key, f'{key}: {json.dumps(adapted_schema[key])}')
                if field_hint:  # Only add non-empty descriptions
                    if current_desc:
                        adapted_schema['description'] = f"{current_desc} | {field_hint}"
                    else:
                        adapted_schema['description'] = field_hint

                unsupported_info.append(f'{key}: {json.dumps(adapted_schema[key])}')

            del adapted_schema[key]

    # Recursively process properties
    if 'properties' in adapted_schema and isinstance(adapted_schema['properties'], dict):
        adapted_schema['properties'] = {
            k: _gemini_schema_adapter(v) for k, v in adapted_schema['properties'].items()
        }

    # Recursively process array items
    if 'items' in adapted_schema:
        if isinstance(adapted_schema['items'], dict):
            adapted_schema['items'] = _gemini_schema_adapter(adapted_schema['items'])
        elif isinstance(adapted_schema['items'], list):
            adapted_schema['items'] = [_gemini_schema_adapter(item) for item in adapted_schema['items']]

    # Handle anyOf, oneOf, allOf (Gemini may not fully support these)
    for key in ['anyOf', 'oneOf', 'allOf']:
        if key in adapted_schema:
            if isinstance(adapted_schema[key], list):
                adapted_schema[key] = [_gemini_schema_adapter(item) for item in adapted_schema[key]]

    # Add technical information to the end of description (for debugging and reference)
    if unsupported_info:
        description = adapted_schema.get('description', '')
        info_str = "; ".join(unsupported_info)

        # Place technical information at the end of description, separated by special markers
        if description and not description.endswith('(Removed for Gemini compatibility:'):
            adapted_schema['description'] = f"{description}\n\n[Technical Info - Removed for Gemini compatibility: {info_str}]"
        elif not description:
            adapted_schema['description'] = f"[Technical Info - Removed for Gemini compatibility: {info_str}]"

    # Finally perform deep cleaning to ensure no missed format fields
    adapted_schema = _deep_clean_schema_formats(adapted_schema)

    return adapted_schema

def convert_claude_to_gemini(request: ClaudeMessagesRequest) -> dict[str, Any]:
    contents = []
    if request.system:
        system_text = request.system if isinstance(request.system, str) else ' '.join(c.text for c in request.system)

        # Enhance system prompt to encourage more active tool usage
        enhanced_system_text = _enhance_system_prompt(system_text, bool(request.tools))

        contents.extend([
            {"role": "user", "parts": [{"text": enhanced_system_text}]},
            {"role": "model", "parts": [{"text": "我理解了您的指令，我会积极主动地使用可用的工具来完成任务。"}]}
        ])

    for msg in request.messages:
        role = "user" if msg.role == "user" else "model"
        parts = []
        if isinstance(msg.content, str):
            parts.append({"text": msg.content})
        elif isinstance(msg.content, list):
            for block in msg.content:
                part_data = None
                if block.type == "text":
                    part_data = {"text": block.text}
                elif block.type == "image":
                    # Handle image content block - convert Claude format to Gemini format
                    if hasattr(block, 'source') and block.source:
                        source = block.source
                        if source.get('type') == 'base64' and source.get('data'):
                            # Convert base64 data to bytes and use Gemini's Part.from_bytes format
                            import base64
                            from google.genai import types

                            try:
                                image_bytes = base64.b64decode(source.get('data'))
                                mime_type = source.get('media_type', 'image/png')

                                # Create Gemini Part object for image
                                image_part = types.Part.from_bytes(
                                    data=image_bytes,
                                    mime_type=mime_type
                                )

                                # Add the Part object directly to the parts list
                                parts.append(image_part)
                                print(f"🖼️ Image content detected - MIME type: {mime_type}, Data length: {len(image_bytes)} bytes")
                                continue  # Skip the normal part_data processing

                            except Exception as e:
                                print(f"❌ Failed to process image: {e}")
                                continue
                        else:
                            print(f"⚠️ Unsupported image source format: {source}")
                    else:
                        print(f"⚠️ Image block missing source data: {block}")
                elif block.type == "tool_use":
                    part_data = {"function_call": {"name": block.name, "args": block.input}}
                elif block.type == "tool_result":
                    part_data = {"function_response": {"name": block.tool_use_id, "response": {"result": block.content}}}

                # Add thought signature if present (for thinking models in multi-turn conversations)
                thought_signature = getattr(block, 'thought_signature', None)
                if part_data and thought_signature:
                    part_data["thought_signature"] = thought_signature
                    print(f"🧠 Thought signature detected and included in request: {thought_signature[:50]}...")

                if part_data:
                    parts.append(part_data)
        if parts:
            contents.append({"role": role, "parts": parts})

    gemini_request_data: dict[str, Any] = {"contents": contents}

    if request.tools:
        adapted_tools = []
        for tool in request.tools:
            original_schema = tool.input_schema if tool.input_schema else {}
            adapted_schema = _gemini_schema_adapter(original_schema) if original_schema else {}

            # Create information preservation summary
            if original_schema:
                info_summary = _create_information_summary(original_schema, adapted_schema)
                if info_summary:
                    logger.info(f"Tool '{tool.name}' information preservation: {info_summary}")

            # Debug logs: record schema comparison before and after adaptation
            if original_schema:
                logger.debug(f"Tool '{tool.name}' original schema: {json.dumps(original_schema, indent=2, ensure_ascii=False)}")
            logger.debug(f"Tool '{tool.name}' adapted schema: {json.dumps(adapted_schema, indent=2, ensure_ascii=False)}")

            # Verify that adapted schema doesn't contain unsupported fields
            def _validate_schema(schema_obj, path=""):
                if isinstance(schema_obj, dict):
                    unsupported_found = []
                    unsupported_fields = {
                        'exclusiveMinimum', 'exclusiveMaximum', 'multipleOf', 'const',
                        'contentEncoding', 'contentMediaType', 'examples', 'default',
                        'readOnly', 'writeOnly', 'deprecated', '$schema', 'additionalProperties',
                        'patternProperties', 'dependencies'
                    }
                    for key, value in schema_obj.items():
                        current_path = f"{path}.{key}" if path else key
                        if key in unsupported_fields:
                            unsupported_found.append(current_path)
                        elif key == 'format' and schema_obj.get('type') == 'string' and value not in ['enum', 'date-time']:
                            unsupported_found.append(f"{current_path} (unsupported format: {value})")
                        else:
                            unsupported_found.extend(_validate_schema(value, current_path))
                    return unsupported_found
                elif isinstance(schema_obj, list):
                    unsupported_found = []
                    for i, item in enumerate(schema_obj):
                        unsupported_found.extend(_validate_schema(item, f"{path}[{i}]"))
                    return unsupported_found
                return []

            validation_issues = _validate_schema(adapted_schema)
            if validation_issues:
                logger.warning(f"Tool '{tool.name}' still contains unsupported fields after adaptation: {validation_issues}")

            # Enhance tool descriptions to encourage Gemini to use tools more actively
            enhanced_description = _enhance_tool_description(tool.name, tool.description or "")

            adapted_tools.append({
                "function_declarations": [{
                    "name": tool.name,
                    "description": enhanced_description,
                    "parameters": adapted_schema
                }]
            })

        gemini_request_data['tools'] = adapted_tools

    if request.tool_choice:
        mode_map = {'any': 'ANY', 'auto': 'AUTO', 'none': 'NONE'}
        choice_type = request.tool_choice.get('type')
        if choice_type in mode_map:
            gemini_request_data['tool_config'] = {"function_calling_config": {"mode": mode_map[choice_type]}}
        elif choice_type == 'tool':
            gemini_request_data['tool_config'] = {"function_calling_config": {"mode": "ONE", "allowed_function_names": [request.tool_choice.get('name')]}}

        # Log function calling configuration for debugging
        print(f"🔧 Function calling mode configured: {gemini_request_data.get('tool_config', {})}")

    config_fields = {
        'temperature': 'temperature',
        'max_tokens': 'max_output_tokens',
        'top_p': 'top_p',
        'top_k': 'top_k',
        'stop_sequences': 'stop_sequences'
    }
    gen_config = {gemini_key: getattr(request, claude_key) for claude_key, gemini_key in config_fields.items() if getattr(request, claude_key, None) is not None}
    if gen_config:
        gemini_request_data['generation_config'] = gen_config

    # Handle thinking configuration for Gemini 2.5 models
    from src.core.config import config

    # Check if thinking should be enabled
    thinking_enabled = False
    if request.thinking:
        thinking_enabled = request.thinking.enabled
    elif config.enable_thinking_by_default:
        thinking_enabled = True
        print(f"🧠 Thinking enabled by default configuration")

    if thinking_enabled:
        thinking_config = {}

        # Map thinking budget - different defaults for big/small models
        if request.thinking and hasattr(request.thinking, 'budget') and request.thinking.budget is not None:
            thinking_config['thinking_budget'] = request.thinking.budget
            print(f"🧠 Using custom thinking budget: {request.thinking.budget}")
        else:
            # Choose budget based on model type
            model_name = request.model.lower()

            # Determine if this is a big model (Pro/Opus/Sonnet) or small model (Haiku/Flash)
            if any(keyword in model_name for keyword in ['pro', 'opus', 'sonnet', 'big']):
                thinking_config['thinking_budget'] = config.big_model_thinking_budget
                print(f"🧠 Using big model thinking budget: {config.big_model_thinking_budget}")
            else:
                thinking_config['thinking_budget'] = config.small_model_thinking_budget
                print(f"🧠 Using small model thinking budget: {config.small_model_thinking_budget}")

        # Include thoughts summary if requested
        if request.thinking and hasattr(request.thinking, 'include_thoughts') and request.thinking.include_thoughts:
            thinking_config['include_thoughts'] = True

        if thinking_config:
            gemini_request_data['thinking_config'] = thinking_config
            print(f"🧠 Thinking configuration: {thinking_config}")
    else:
        print(f"🧠 Thinking disabled for this request")

    return gemini_request_data

# OpenAI helper functions removed - project now focuses on Gemini API only
