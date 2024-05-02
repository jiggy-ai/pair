from typing import List, Callable, Optional, Union, Literal
from pydantic import BaseModel, ValidationError, Field, validator, root_validator


DetailType = Literal['high', 'low']

class ImageUrl(BaseModel):
    url: str
    detail: DetailType

    @validator('detail')
    def check_detail(cls, value):
        allowed_details = set(DetailType.__args__)
        if value not in allowed_details:
            raise ValueError(f'detail must be one of {allowed_details}, got {value}')
        return value

    
MsgContentType = Literal["text", "image_url"]

class MessageContent(BaseModel):
    type:      MsgContentType
    text:      Optional[str]
    image_url: Optional[ImageUrl]
    
    @validator('type')
    def check_type(cls, value):
        allowed_types = set(MsgContentType.__args__)
        if value not in allowed_types:
            raise ValueError(f'type must be one of {allowed_types}, got {value}')
        return value

    @root_validator
    def check_content(cls, values):
        content_type, text, image_url = values.get('type'), values.get('text'), values.get('image_url')
        if content_type == 'text' and not text:
            raise ValueError('text must be provided when type is "text"')
        elif content_type == 'image_url' and not image_url:
            raise ValueError('image_url must be provided when type is "image_url"')
        return values


MsgRoleType = Literal["system", "user", "assistant"]

class ChatCompletionMessage(BaseModel):
    """
    OpenAI Chat Completion Message    
    """
    role    : MsgRoleType 
    content : Union[str, List[MessageContent]]
    
    @validator('role')
    def check_role(cls, value):
        allowed_roles = set(MsgRoleType.__args__)
        if value not in allowed_roles:
            raise ValueError(f'role must be one of {allowed_roles}, got {value}')
        return value
    

class CompletionRequest(BaseModel):
    """
    OpenAI Chat Completion Request
    """
    model: str
    messages: list[ChatCompletionMessage]
    max_tokens: Optional[int] 
    temperature: float
    stream: bool

class Choice(BaseModel):
    finish_reason: str
    index: int
    message: ChatCompletionMessage

class Usage(BaseModel):
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int

class ChatCompletion(BaseModel):
    id: str
    choices: List[Choice]
    created: int
    model: str
    object: str
    usage: Usage

    def __str__(self):
        return self.choices[0].message.content
