from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime
import uuid

from src.core.config import config
from src.core.logging import logger
from src.core.gemini_client import GeminiClient
from src.models.claude import ClaudeMessagesRequest, ClaudeTokenCountRequest
from src.conversion.request_converter import convert_claude_to_gemini
from src.conversion.response_converter import (
    convert_gemini_to_claude_response,
    convert_gemini_to_claude_stream_response
)
from src.core.model_manager import model_manager

router = APIRouter()

# Initialize Gemini client only
gemini_client = GeminiClient()

@router.post("/v1/messages")
async def create_message(request: ClaudeMessagesRequest, http_request: Request):
    try:
        request_id = str(uuid.uuid4())
        model_info = model_manager.get_model_info(request.model)
        api_type = model_info.get("api_type")
        target_model = model_info.get("model_name")

        if not api_type or not target_model:
            raise HTTPException(status_code=400, detail=f"Model '{request.model}' not found or not configured.")

        logger.debug(
            f"Processing request {request_id} for model {request.model} -> mapped to {api_type.upper()} model {target_model}"
        )

        if await http_request.is_disconnected():
            raise HTTPException(status_code=499, detail="Client disconnected")

        # Project now only supports Gemini API
        if api_type != "gemini":
            raise HTTPException(status_code=400, detail=f"API type '{api_type}' not supported. Only Gemini API is supported.")

        client = gemini_client
        api_request = convert_claude_to_gemini(request)
        api_request['model'] = target_model # Add model name for Gemini client

        if request.stream:
            api_stream = client.create_chat_completion_stream(api_request, request_id)
            return StreamingResponse(
                convert_gemini_to_claude_stream_response(api_stream, request.model, request_id),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",  # Disable nginx buffering
                    "X-Content-Type-Options": "nosniff",  # Prevent content sniffing
                    "Transfer-Encoding": "chunked"  # Force chunked encoding
                }
            )
        else:
            api_response = await client.create_chat_completion(api_request, request_id)
            claude_response = convert_gemini_to_claude_response(api_response, request.model, request_id)
            return JSONResponse(content=claude_response)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error processing request: {e}")
        logger.error(traceback.format_exc())
        # Use a generic error classifier if client-specific one is not available
        error_message = str(e)
        raise HTTPException(status_code=500, detail=error_message)

# The rest of the file (health checks, etc.) remains the same.
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "gemini_api_configured": bool(config.gemini_api_key),
        "api_type": "gemini_only"
    }
