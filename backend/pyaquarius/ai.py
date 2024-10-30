import asyncio
import base64
import logging
import os
from functools import wraps
from typing import Any, Callable, Dict, List
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

log = logging.getLogger(__name__)


AI_API_TIMEOUT: int = int(os.getenv('AI_API_TIMEOUT', '30'))
AI_API_MAX_RETRIES: int = int(os.getenv('AI_API_MAX_RETRIES', '3'))
AI_MAX_TOKENS: int = int(os.getenv('AI_MAX_TOKENS', '1000'))
ENABLED_MODELS: List[str] = []

try:
    from anthropic import Anthropic
    if os.getenv('ANTHROPIC_API_KEY'):
        ENABLED_MODELS.append('claude')
    else:
        log.warning("ANTHROPIC_API_KEY not set - Claude service will be unavailable")
except ImportError:
    log.warning("anthropic module not installed - Claude service will be unavailable")

try:
    from openai import OpenAI
    if os.getenv('OPENAI_API_KEY'):
        ENABLED_MODELS.append('gpt4v')
    else:
        log.warning("OPENAI_API_KEY not set - GPT-4V service will be unavailable") 
except ImportError:
    log.warning("openai module not installed - GPT-4V service will be unavailable")

try:
    import google.generativeai as genai
    if os.getenv('GOOGLE_API_KEY'):
        ENABLED_MODELS.append('gemini')
    else:
        log.warning("GOOGLE_API_KEY not set - Gemini service will be unavailable")
except ImportError:
    log.warning("google-generativeai module not installed - Gemini service will be unavailable")



def encode_image(image_path: str) -> str:
    """Encode image to base64 string."""
    if not os.path.exists(image_path):
        raise ValueError(f"Image file not found: {image_path}")
    
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to encode image: {str(e)}")

def ai_retry_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
    @retry(
        stop=stop_after_attempt(AI_API_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        reraise=True
    )
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=AI_API_TIMEOUT)
        except asyncio.TimeoutError as e:
            log.error(f"Timeout in {func.__name__}: {str(e)}")
            raise TimeoutError(f"{func.__name__} timed out after {AI_API_TIMEOUT} seconds")
    return wrapper

@ai_retry_decorator
async def claude(prompt: str, image_path: str) -> str:
    """Call Claude 3.5 Sonnet API with image."""
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        base64_image = encode_image(image_path)
        client = Anthropic(api_key=api_key)
        log.info("Calling Claude API")
        log.debug(f"Prompt: {prompt}")
        response = await client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=AI_MAX_TOKENS,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64_image,
                        },
                    },
                ],
            }]
        )
        response = response.content[0].text
        log.info("Claude API responded")
        log.debug(f"Response: {response}")
        return response
    except Exception as e:
        log.error(f"Claude API error: {str(e)}")
        return f"Claude API error: {str(e)}"

@ai_retry_decorator
async def gpt4o_mini(prompt: str, image_path: str) -> str:
    """Call GPT-4o-mini API with image and prompt."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        client = OpenAI(api_key=api_key)
        base64_image = encode_image(image_path)
        log.info("Calling GPT-4o-mini API")
        log.debug(f"Prompt: {prompt}")
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            max_tokens=AI_MAX_TOKENS,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        },
                    ],
                }
            ],
        )
        response = response.choices[0].message.content
        log.info("GPT-4o-mini API responded")
        log.debug(f"Response: {response}")
        return response

    except Exception as e:
        log.error(f"GPT-4o-mini API error: {str(e)}")
        return f"GPT-4o-mini API error: {str(e)}"

@ai_retry_decorator
async def gemini(prompt: str, image_path: str) -> str:
    """Call Google Gemini API with image using the File API."""
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not set")
        genai.configure(api_key=api_key)
        uploaded_file = genai.upload_file(image_path)
        log.info(f"Uploaded file to Gemini: {uploaded_file.uri}")
        model = genai.GenerativeModel(model_name='gemini-1.5-flash')
        response = await model.generate_content_async(
            [uploaded_file, "\n\n", prompt],
            request_options={"timeout": 600},
            generation_config={"max_output_tokens": AI_MAX_TOKENS},
        )
        response = response.text
        log.info("Gemini API responded")
        log.debug(f"Response: {response}")
        return response

    except Exception as e:
        log.error(f"Gemini API error: {str(e)}")
        return f"Gemini API error: {str(e)}"

AI_MODEL_MAP: Dict[str, callable] = {
    'claude': claude,
    'gpt': gpt4o_mini,
    'gemini': gemini
}

async def async_identify_life(ai_model: str, image_path: str) -> Dict[str, str]:
    """Identify life in an image."""
    prompt = "Identify any fish, invertebrates, and plants in this underwater image of an aquarium. Use the attached csv to confirm your identifications. Return only the life you can identify in the image. Return your answers in the same csv format as the attached csv.\n"
    with open(os.path.join(os.path.dirname(__file__), "ainotes", "life.csv")) as f:
        header = next(f)
        prompt += f"{header}\n"
        prompt += f.read()
    response = await AI_MODEL_MAP[ai_model](prompt, image_path)
    reader = csv.reader(response.splitlines())
    assert next(reader) == header.split(',')
    life_filepath = os.path.join(os.path.dirname(__file__), "ainotes", f"life_{ai_model}_{datetime.now().isoformat()}.csv")
    with open(life_filepath, "w") as f:
        writer = csv.writer(f)
        writer.writerows(reader)
    return response


async def async_estimate_temperature(ai_model: str, image_path: str) -> Dict[str, str]:
    """Estimate the temperature of the water in an image."""
    prompt = "Estimate the temperature of the water in this underwater image of an aquarium. Use the red digital submersible thermometer visible in the image.\n"
    return await AI_MODEL_MAP[ai_model](prompt, image_path)


AI_ANALYSES_MAP: Dict[str, callable] = {
    'identify_life': async_identify_life,
    'estimate_temperature': async_estimate_temperature,
}

async def async_inference(ai_models: List[str], analyses: List[str], image_path: str) -> Dict[str, str]:
    """Perform many AI analyses with multiple AI apis asynchronously."""
    try:
        if not ENABLED_MODELS:
            raise ValueError("No AI apis enabled")
        
        tasks = []
        task_keys = []
        for ai_model in ai_models:
            if ai_model not in ENABLED_MODELS:
                raise ValueError(f"Model {ai_model} not enabled")
            for analysis in analyses:
                if analysis not in AI_ANALYSES_MAP:
                    raise ValueError(f"Analysis {analysis} not found in AI_ANALYSES_MAP")
                tasks.append(AI_ANALYSES_MAP[analysis](ai_model, image_path))
                task_keys.append(f"{ai_model}.{analysis}")
        
        if not tasks:
            raise ValueError("No enabled models found in model map")
            
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            key: resp if not isinstance(resp, Exception) else str(resp)
            for key, resp in zip(task_keys, responses)
        }
        
    except Exception as e:
        log.error(f"ai api inference error: {str(e)}")
        return {"error": f"ai api inference failed: {str(e)}"}
