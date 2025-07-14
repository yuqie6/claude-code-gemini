from google import genai
from google.genai import types
import json
import traceback
import hashlib
import datetime
import os
import pickle
from typing import Any, AsyncGenerator, List, Optional
from fastapi import HTTPException

from src.core.base_client import BaseAPIClient
from src.core.config import config

class GeminiClient(BaseAPIClient):
    """Client for interacting with the Google Gemini API using the latest SDK patterns."""

    def __init__(self):
        if not config.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Cache management with persistence
        self._cache_file = "gemini_cache_store.pkl"
        self._cache_store = self._load_cache_store()

        # Cache configuration from config
        self._cache_enabled = config.enable_content_cache
        self._cache_min_chars = config.cache_min_chars
        self._default_cache_ttl = config.cache_ttl_hours * 60 * 60  # Convert hours to seconds
        self._max_cache_ttl = 7 * 24 * 60 * 60  # 7 days maximum

        # 配置Gemini客户端（自定义端点或官方端点）
        if config.gemini_base_url:
            print(f"🔧 使用自定义Gemini端点: {config.gemini_base_url}")
            # 通过HttpOptions直接设置base_url
            http_options = types.HttpOptions(
                base_url=config.gemini_base_url
            )
            self.client = genai.Client(
                api_key=config.gemini_api_key,
                http_options=http_options
            )
        else:
            print(f"� 使用官方Gemini端点")
            self.client = genai.Client(
                api_key=config.gemini_api_key
            )

    def _load_cache_store(self) -> dict:
        """Load cache store from persistent storage."""
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, 'rb') as f:
                    cache_store = pickle.load(f)
                    # Clean expired caches
                    now = datetime.datetime.now(datetime.timezone.utc)
                    valid_caches = {}
                    for key, cache_info in cache_store.items():
                        if now < cache_info['expire_time']:
                            valid_caches[key] = cache_info
                        else:
                            print(f"🗄️ Removing expired cache: {key}")
                    print(f"🗄️ Loaded {len(valid_caches)} valid caches from storage")
                    return valid_caches
        except Exception as e:
            print(f"⚠️ Failed to load cache store: {str(e)}")
        return {}

    def _save_cache_store(self):
        """Save cache store to persistent storage."""
        try:
            with open(self._cache_file, 'wb') as f:
                pickle.dump(self._cache_store, f)
        except Exception as e:
            print(f"⚠️ Failed to save cache store: {str(e)}")

    def _generate_cache_key(self, content: str, model: str) -> str:
        """Generate a unique cache key for content."""
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
        return f"cache_{model}_{content_hash}"

    def _should_use_cache(self, content: str) -> bool:
        """Determine if content should be cached based on configuration."""
        if not self._cache_enabled:
            return False
        return len(content) > self._cache_min_chars

    def _check_content_cache(self, content: str, model: str) -> Optional[str]:
        """Check if we've seen this content before (client-side cache)."""
        cache_key = self._generate_cache_key(content, model)

        # Reduced cache check logging

        if cache_key in self._cache_store:
            cache_info = self._cache_store[cache_key]
            # Check if cache is still valid
            if datetime.datetime.now(datetime.timezone.utc) < cache_info['expire_time']:
                print(f"🗄️ Cache HIT: {cache_key[:16]}...")
                # Increment hit count
                cache_info['hit_count'] = cache_info.get('hit_count', 0) + 1
                self._save_cache_store()
                return cache_key
            else:
                # Cache expired, remove it
                del self._cache_store[cache_key]
                self._save_cache_store()
                print(f"🗄️ Cache EXPIRED: {cache_key[:16]}...")
        # No need to log cache miss

        return None

    def _store_content_cache(self, content: str, model: str) -> str:
        """Store content in client-side cache."""
        cache_key = self._generate_cache_key(content, model)

        expire_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=self._default_cache_ttl)
        self._cache_store[cache_key] = {
            'content': content,  # Store the actual content for client-side cache
            'expire_time': expire_time,
            'content_hash': cache_key,
            'model': model,
            'created_at': datetime.datetime.now(datetime.timezone.utc),
            'hit_count': 1
        }

        # Save to persistent storage
        self._save_cache_store()

        print(f"🗄️ Cache STORED: {cache_key[:16]}...")
        return cache_key

    def _create_cache_placeholder(self, content: str) -> str:
        """Create a placeholder for cached content."""
        # Create a short summary of the cached content
        content_preview = content[:100] + "..." if len(content) > 100 else content
        return f"[CACHED_CONTENT: {len(content)} chars - {content_preview}]"

    def get_cache_stats(self) -> dict:
        """Get cache statistics for monitoring."""
        now = datetime.datetime.now(datetime.timezone.utc)
        active_caches = 0
        expired_caches = 0

        for cache_info in self._cache_store.values():
            if now < cache_info['expire_time']:
                active_caches += 1
            else:
                expired_caches += 1

        return {
            'active_caches': active_caches,
            'expired_caches': expired_caches,
            'total_caches': len(self._cache_store)
        }

    def _prepare_config(self, request: dict[str, Any]) -> types.GenerateContentConfig:
        """Helper to construct the GenerateContentConfig object from the request."""
        generation_config_dict = request.pop("generation_config", {})
        filtered_config = {k: v for k, v in generation_config_dict.items() if v is not None}

        # 处理工具配置 - 使用最新SDK方式
        tools_list = []
        request_tools = request.get('tools')
        if request_tools:
            for tool_def in request_tools:
                # 支持两种格式：function_declarations 和 functionDeclarations
                func_decls = tool_def.get('function_declarations') or tool_def.get('functionDeclarations')
                if func_decls:
                    # 创建Tool对象，使用types.Tool
                    function_declarations = []
                    for func_decl in func_decls:
                        # 创建FunctionDeclaration对象
                        func_declaration = types.FunctionDeclaration(
                            name=func_decl['name'],
                            description=func_decl.get('description', ''),
                            parameters=func_decl.get('parameters', {})
                        )
                        function_declarations.append(func_declaration)

                    # 创建Tool对象
                    tool = types.Tool(function_declarations=function_declarations)
                    tools_list.append(tool)

        # 处理tool_config
        tool_config = None
        if request.get('tool_config'):
            tool_config_data = request['tool_config']
            if tool_config_data.get('function_calling_config'):
                func_config = tool_config_data['function_calling_config']
                tool_config = types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode=func_config.get('mode', 'AUTO'),
                        allowed_function_names=func_config.get('allowed_function_names')
                    )
                )

        # Handle thinking configuration for Gemini 2.5 models
        thinking_config = None
        if request.get('thinking_config'):
            thinking_data = request['thinking_config']
            thinking_config = types.ThinkingConfig(
                thinking_budget=thinking_data.get('thinking_budget'),
                include_thoughts=thinking_data.get('include_thoughts', False)
            )
            print(f"🧠 Thinking config prepared: budget={thinking_data.get('thinking_budget')}, include_thoughts={thinking_data.get('include_thoughts', False)}")

        return types.GenerateContentConfig(
            tools=tools_list if tools_list else None,
            tool_config=tool_config,
            thinking_config=thinking_config,
            safety_settings=request.get('safety_settings'),
            **filtered_config
        )

    def _response_to_dict(self, response) -> dict[str, Any]:
        """Manually and safely convert the response object to a dictionary."""
        candidates = []
        if hasattr(response, 'candidates') and response.candidates:
            for cand in response.candidates:
                parts = []
                if hasattr(cand, 'content') and cand.content and hasattr(cand.content, 'parts') and cand.content.parts:
                    for part in cand.content.parts:
                        part_dict = {}
                        if hasattr(part, 'text') and part.text:
                            part_dict['text'] = part.text
                        if hasattr(part, 'function_call') and part.function_call:
                            part_dict['function_call'] = {'name': part.function_call.name, 'args': dict(part.function_call.args)}

                        # Handle thinking-related fields
                        if hasattr(part, 'thought') and part.thought:
                            part_dict['thought'] = part.thought
                            print(f"🧠 Thought summary detected in response")
                        if hasattr(part, 'thought_signature') and part.thought_signature:
                            part_dict['thought_signature'] = part.thought_signature
                            print(f"🧠 Thought signature detected in response")

                        parts.append(part_dict)
                
                finish_reason_name = None
                if hasattr(cand, 'finish_reason') and cand.finish_reason:
                    finish_reason_name = cand.finish_reason.name

                candidates.append({
                    'content': {'parts': parts, 'role': cand.content.role if hasattr(cand, 'content') and cand.content else 'model'},
                    'finish_reason': finish_reason_name,
                })
        
        usage_metadata = None
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            prompt_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
            candidates_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)

            # Handle thinking tokens if present
            thoughts_tokens = getattr(response.usage_metadata, 'thoughts_token_count', 0)

            # Ensure thoughts_tokens is not None to avoid comparison errors
            if thoughts_tokens is None:
                thoughts_tokens = 0

            usage_metadata = {
                'prompt_token_count': prompt_tokens,
                'candidates_token_count': candidates_tokens,
            }

            # Add thinking tokens if present
            if thoughts_tokens > 0:
                usage_metadata['thoughts_token_count'] = thoughts_tokens
                print(f"🧠 Thinking tokens: {thoughts_tokens}")

            # Only log token extraction in non-streaming mode to avoid spam
            # (streaming mode logs are handled in response_converter.py)
            # print(f"🔍 Gemini usage_metadata extracted - Prompt tokens: {prompt_tokens}, Candidates tokens: {candidates_tokens}")

        return {
            'candidates': candidates,
            'usage_metadata': usage_metadata,
        }

    async def create_chat_completion(
        self, request: dict[str, Any], request_id: str
    ) -> dict[str, Any]:
        """Create a non-streaming chat completion with Gemini."""
        model_name = request.pop("model")
        config_obj = self._prepare_config(request)

        # Check for cacheable content and create cache if needed
        contents = request.get('contents', [])

        # Try to identify large system content that can be cached
        if contents and len(contents) > 0:
            first_content = contents[0]

            if (first_content.get('role') == 'user' and
                first_content.get('parts') and
                len(first_content['parts']) > 0):

                first_part = first_content['parts'][0]

                if 'text' in first_part:
                    text_content = first_part['text']
                    should_cache = self._should_use_cache(text_content)

                    if should_cache:
                        # Check client-side cache first
                        cache_hit = self._check_content_cache(text_content, model_name)

                        if cache_hit:
                            # For cache hit, use a much shorter version
                            lines = text_content.split('\n')
                            short_content = '\n'.join(lines[-5:]) if len(lines) > 5 else text_content
                            first_part['text'] = f"[Previous context cached] {short_content}"
                            print(f"🗄️ Using cached content ({len(short_content)} chars vs {len(text_content)} chars)")
                        else:
                            # Store in client-side cache for future use
                            self._store_content_cache(text_content, model_name)

        # Log request summary (reduced verbosity)
        contents_count = len(request.get('contents', []))
        print(f"🚀 Gemini request: {model_name} ({contents_count} content blocks)")

        # Send request to Gemini API (removed fallback logic to avoid duplicate requests)
        try:
            response = await self.client.aio.models.generate_content(
                model=model_name,
                contents=request.get('contents') or [],
                config=config_obj
            )
            return self._response_to_dict(response)
        except Exception as e:
            print(f"❌ Gemini API failed: {str(e)}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

    async def create_chat_completion_stream(
        self, request: dict[str, Any], request_id: str
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Create a streaming chat completion with Gemini."""
        model_name = request.pop("model")
        config_obj = self._prepare_config(request)

        # Check for cacheable content and create cache if needed (same logic as non-streaming)
        contents = request.get('contents', [])

        if contents and len(contents) > 0:
            first_content = contents[0]
            if (first_content.get('role') == 'user' and
                first_content.get('parts') and
                len(first_content['parts']) > 0):

                first_part = first_content['parts'][0]
                if 'text' in first_part:
                    text_content = first_part['text']
                    should_cache = self._should_use_cache(text_content)

                    if should_cache:
                        # Check client-side cache first
                        cache_hit = self._check_content_cache(text_content, model_name)

                        if cache_hit:
                            # For cache hit, use a much shorter version
                            lines = text_content.split('\n')
                            short_content = '\n'.join(lines[-5:]) if len(lines) > 5 else text_content
                            first_part['text'] = f"[Previous context cached] {short_content}"
                            print(f"🗄️ Stream using cached content ({len(short_content)} chars vs {len(text_content)} chars)")
                        else:
                            # Store in client-side cache for future use
                            self._store_content_cache(text_content, model_name)

        # Log streaming request start
        contents_count = len(contents)
        print(f"🌊 Streaming: {model_name} ({contents_count} content blocks)")

        # Send request to Gemini API (removed fallback logic to avoid duplicate requests)
        try:
            stream = await self.client.aio.models.generate_content_stream(
                model=model_name,
                contents=request.get('contents') or [],
                config=config_obj
            )
            async for chunk in stream:
                chunk_dict = self._response_to_dict(chunk)
                yield chunk_dict

        except Exception as e:
            print(f"❌ Gemini streaming API failed: {str(e)}")
            traceback.print_exc()

            # Yield error response in consistent format
            error_response = {
                "type": "error",
                "error": {"type": "api_error", "message": f"Gemini API streaming error: {str(e)}"},
            }
            yield error_response
