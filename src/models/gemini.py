from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, Literal

# Tool and Function Calling Models
class FunctionDeclaration(BaseModel):
    name: str
    description: str
    parameters: Optional[Dict[str, Any]] = None

class Tool(BaseModel):
    function_declarations: List[FunctionDeclaration]

# Function Calling Configuration - 新增的类
class FunctionCallingConfig(BaseModel):
    mode: Literal["AUTO", "ANY", "NONE", "ONE"] = "AUTO"
    allowed_function_names: Optional[List[str]] = None

class ToolConfig(BaseModel):
    function_calling_config: Optional[FunctionCallingConfig] = None

# Content and Part Models
class FunctionCall(BaseModel):
    name: str
    args: Dict[str, Any]
    id: Optional[str] = None

class Part(BaseModel):
    text: Optional[str] = None
    function_call: Optional[FunctionCall] = None
    thought: Optional[bool] = None  # Indicates if this part contains thinking content

class Content(BaseModel):
    parts: List[Part]
    role: Optional[str] = None

# Generation Configuration
class GenerationConfig(BaseModel):
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    top_k: Optional[int] = None
    candidate_count: Optional[int] = None
    max_output_tokens: Optional[int] = None
    stop_sequences: Optional[List[str]] = None

# Safety Settings
class SafetySetting(BaseModel):
    category: str
    threshold: str

# Main Request Model
class GeminiRequest(BaseModel):
    contents: List[Content]
    tools: Optional[List[Tool]] = None
    tool_config: Optional[ToolConfig] = None
    generation_config: Optional[GenerationConfig] = Field(default_factory=GenerationConfig)
    safety_settings: Optional[List[SafetySetting]] = None

# Response Models
class SafetyRating(BaseModel):
    category: str
    probability: str

class PromptFeedback(BaseModel):
    block_reason: Optional[str] = None
    safety_ratings: Optional[List[SafetyRating]] = None

class UsageMetadata(BaseModel):
    prompt_token_count: Optional[int] = None
    candidates_token_count: Optional[int] = None
    total_token_count: Optional[int] = None
    thoughts_token_count: Optional[int] = None  # Thinking tokens for Gemini 2.5 models

class Candidate(BaseModel):
    content: Content
    finish_reason: str
    index: Optional[int] = None
    safety_ratings: Optional[List[SafetyRating]] = None
    token_count: Optional[int] = None

class GeminiResponse(BaseModel):
    candidates: List[Candidate]
    prompt_feedback: Optional[PromptFeedback] = None
    usage_metadata: Optional[UsageMetadata] = None
