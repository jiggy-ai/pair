from typing import List, Callable, Optional
from loguru import logger
import json
from pydantic import BaseModel, ValidationError, Field, validator
from time import time
import os
from openai import OpenAI, RateLimitError, BadRequestError
from findfilt import find_files
from openai_models import ChatCompletionMessage, CompletionRequest

PAIR_MODEL = os.environ.get('PAIR_MODEL', 'gpt-4-turbo-2024-04-09')

client = OpenAI()



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
                         input_tokens    = 0,   #  sum([msg.tokens for msg in msgs]) + 2 , # XXX calculate tokesn
                         response_tokens = 0,
                         price           = 0)

    creq = CompletionRequest(model=model, messages=messages, temperature=temperature, max_tokens=2048, stream=True)

    #print(creq.json(indent=4))
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
    response_tokens = 0 ### calculate tokens
    #cr.price = price(model, cr.input_tokens, resp_msg.tokens)
    yield resp

