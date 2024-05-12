from typing import List, Callable, Optional
from loguru import logger
import json
from pydantic import BaseModel, ValidationError, Field, validator
from time import time
import os
from openai import OpenAI, RateLimitError, BadRequestError
from findfilt import find_files
from openai_models import ChatCompletionMessage, CompletionRequest
from PIL import Image
from typing import Tuple
import tiktoken
import io 
import base64

PAIR_MODEL = os.environ.get('PAIR_MODEL', 'gpt-4-turbo-2024-04-09')

client = OpenAI()

enc = tiktoken.get_encoding("cl100k_base")

    
class ChatResponse(BaseModel):
    """
    contains the complete state of the input context as sent to the model as well as the response from the model
    and other details such as the model used, the number of tokens used, and the estimated cost of the request
    """
    text:               str                             # the completion response from the model
    delta:              Optional[str]                   # the response text delta for streaming case
    model:              str                             # the model used to generate the response
    temperature:        float                           # the temperature used to generate the response
    inputs:             List[ChatCompletionMessage]     # the input context as sent to the model    
    input_tokens:       int                             # the number of tokens used in the input context
    response_tokens:    int                             # the number of tokens in the response text.  only valid on last output for streaming
    price:              float                           # the estimated price of the request in dollars. only valid on last output for streaming

    


def price(model, input_tokens, output_tokens):
    # https://openai.com/pricing
    if model in ['gpt-3.5-turbo', 'gpt-3.5']:
        tokens = input_tokens + output_tokens
        dollars = 0.002 * tokens / 1000
    elif model == 'gpt-4':
        dollars =  (.03*input_tokens + .06*output_tokens) / 1000
    elif model in ['gpt-4-1106-preview', 'gpt-4-turbo-2024-04-09']:
        dollars =  (.01*input_tokens + .03*output_tokens) / 1000
    else:
        raise ValueError(f"model {model} not supported")
    return dollars



def gpt4_high_image_tokens_from_url(url: str) -> int:

    # url is of the form data:{mime_type};base64,{encoded_image}
    mime_type, encoded_image = url.split(';base64,')
    #decode the base64 encoded image
    image = base64.b64decode(encoded_image)            
    
    with Image.open(io.BytesIO(image)) as img:
        width, height = img.size

    max_dim = max(width, height)
    if max_dim > 2048:
        ratio = 2048 / max_dim
    width = int(width * ratio)
    height = int(height * ratio)

    min_dim = min(width, height)
    # scale minimum to 768
    ratio = 768 / min_dim
    width = int(width * ratio)
    height = int(height * ratio)

    # calculate number of 512x512 tiles, rounding up
    x_tiles = (width + 511) // 512
    y_tiles = (height + 511) // 512
    
    # 85 tokens plus 170 tokens per 512x512 tile
    return 85 + 170 * x_tiles * y_tiles 


def message_tokens(msg: ChatCompletionMessage) -> int:
    if type(msg.content) == str:
        _text = f'{msg.role}\n{msg.content}'
        return len(enc.encode(msg.content)) + 4

    assert type(msg.content) == list
    tokens = len(enc.encode(msg.role+"\n")) + 4    
    for mc in msg.content:
        if mc.type == 'text':
            tokens += len(enc.encode(mc.text)) 
        elif mc.type == 'image_url':
            tokens += gpt4_high_image_tokens_from_url(mc.image_url.url)
        else:
            raise ValueError(f"unknown message content type {mc.type}")
    return tokens


def completions(messages       : List[ChatCompletionMessage],
                model          : str = 'gpt-4-turbo-2024-04-09',
                temperature    : float = 0):

    """
    return tuple of (delta, response, done):  
    where delta is the incremental response text,
    response is the cumulative response text,
    and done is True if the completion is complete
    """
    resp = ChatResponse(text            = "",
                         delta           = "",
                         model           = model,
                         temperature     = temperature,
                         inputs          = messages,
                         input_tokens    = sum([message_tokens(m) for m in messages]) + 2, 
                         response_tokens = 0,
                         price           = 0)

    creq = CompletionRequest(model=model, messages=messages, temperature=temperature, stream=True)
        
    try:
        response = client.chat.completions.create(**creq.dict(exclude_none=True))

        for chunk in response:
            output = chunk.choices[0].delta.content or ''
            if output:
                resp.delta = output
                resp.text += output
                yield resp

    except RateLimitError as e:   
        logger.warning(f"OpenAI RateLimitError: {e}")
        raise
    except BadRequestError as e: # too many token
        logger.error(f"OpenAI BadRequestError: {e}")
        raise
    except Exception as e:
        logger.exception(e)
        raise
    resp.response_tokens = len(enc.encode(resp.text))
    resp.price = price(model, resp.input_tokens, resp.response_tokens)
    yield resp


ValidatorFunctionType = Callable[[BaseModel, str], None]

def extract_dataclass(messages       : List[ChatCompletionMessage],
                            data_model     : BaseModel,                 
                            retry          : int = 3,
                            model          : str = 'gpt-4-turbo-2024-04-09',
                            temperature    : float = 0,                            
                            task_validator : Optional[ValidatorFunctionType] = None) -> BaseModel:

    ts = int(time()*1000)    
    logger.info(f"extract_dataclass: data_model={data_model.__name__} dump timestamp = {ts}")
    
    pydantic_instruction  = "Please respond ONLY with raw valid json that conforms to this pydantic json_schema:\n" 
    pydantic_instruction += f" {data_model.schema_json()} \n" 
    pydantic_instruction += "Do not include additional text other than the object json as we will load this object with json.loads() and pydantic."
    messages.append(ChatCompletionMessage(role="system", content=pydantic_instruction))
        
    last_exception = None        
    for i in range(retry+1):
          
        cr = CompletionRequest(model=model, messages=messages, temperature=temperature, stream=False)      
            
        response = client.chat.completions.create(**cr.dict())
        assistant_message = response.choices[0].message
        content = assistant_message.content

        if content.startswith("```json"):
            content = content[7:-3]  # just get the json content without hassling the model about it
            
        try:
            json_content = json.loads(content)
        except Exception as e:
            last_exception = e
            error_msg = f"json.loads exception: {e}"
            logger.error(error_msg)
            messages.append(assistant_message)
            messages.append({"role"   : "system",
                            "content" : error_msg})
            continue
  
        try:
            data_model =  data_model(**json_content)
        except ValidationError as e:
            last_exception = e
            error_msg = f"pydantic exception: {e}"
            logger.warning(error_msg)
            messages.append(assistant_message)
            messages.append({"role"   : "system",
                            "content" : error_msg})
            continue
                
        if task_validator:
            try:
                task_validator(data_model, content)
            except ValidationError as e:
                last_exception = e
                error_msg = f"validation exception: {e}"
                logger.warning(error_msg)
                messages.append(assistant_message)            
                messages.append({"role"    : "system",
                                 "content" : error_msg})
        logger.info(data_model.json())
        return data_model
    # end retry loop
    logger.error(f"Failed to extract dataclass after {retry} attempts")
    raise last_exception


