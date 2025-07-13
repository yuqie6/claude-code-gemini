from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, Literal

class ClaudeContentBlockText(BaseModel):
    type: Literal["text"]
    text: str

class ClaudeContentBlockImage(BaseModel):
    type: Literal["image"]
    source: Dict[str, Any]

class ClaudeContentBlockToolUse(BaseModel):
    type: Literal["tool_use"]
    id: str
    name: str
    input: Dict[str, Any]

class ClaudeContentBlockToolResult(BaseModel):
    type: Literal["tool_result"]
    tool_use_id: str
    content: Union[str, List[Dict[str, Any]], Dict[str, Any]]

class ClaudeSystemContent(BaseModel):
    type: Literal["text"]
    text: str

class ClaudeMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: Union[str, List[Union[ClaudeContentBlockText, ClaudeContentBlockImage, ClaudeContentBlockToolUse, ClaudeContentBlockToolResult]]]

class ClaudeTool(BaseModel):
    name: str
    description: Optional[str] = None
    input_schema: Dict[str, Any]

class ClaudeThinkingConfig(BaseModel):
    enabled: bool = True
    budget: Optional[int] = None  # Thinking token budget (-1 for dynamic, 0 to disable, >0 for specific amount)
    include_thoughts: bool = False  # Whether to include thought summaries in response

class ClaudeMessagesRequest(BaseModel):
    model: str
    max_tokens: int
    messages: List[ClaudeMessage]
    system: Optional[Union[str, List[ClaudeSystemContent]]] = None
    stop_sequences: Optional[List[str]] = None
    stream: Optional[bool] = False
    temperature: Optional[float] = 1.0
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    tools: Optional[List[ClaudeTool]] = None
    tool_choice: Optional[Dict[str, Any]] = None
    thinking: Optional[ClaudeThinkingConfig] = None

class ClaudeTokenCountRequest(BaseModel):
    model: str
    messages: List[ClaudeMessage]
    system: Optional[Union[str, List[ClaudeSystemContent]]] = None
    tools: Optional[List[ClaudeTool]] = None
    thinking: Optional[ClaudeThinkingConfig] = None
    tool_choice: Optional[Dict[str, Any]] = None

# Response Models - 新增的响应类
class ContentBlock(BaseModel):
    type: Literal["text", "tool_use"]
    text: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None  # For additional information like thought summaries
    thought_signature: Optional[str] = None  # Thought signature for thinking models in multi-turn conversations

class Usage(BaseModel):
    input_tokens: int
    output_tokens: int
    cache_read_input_tokens: Optional[int] = None
    thoughts_token_count: Optional[int] = None  # Thinking token count for thinking models

class ClaudeMessagesResponse(BaseModel):
    id: str
    type: Literal["message"] = "message"
    role: Literal["assistant"] = "assistant"
    model: str
    content: List[ContentBlock]
    stop_reason: Optional[str] = None
    usage: Usage
