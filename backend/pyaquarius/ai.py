import asyncio
import base64
import csv
import logging
import os
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable, Dict, List

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from pyaquarius.models import DBAIAnalysis, DBImage, DBLife, DBReading, get_db_session

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
        ENABLED_MODELS.append('gpt')
    else:
        log.warning("OPENAI_API_KEY not set - GPT service will be unavailable") 
except ImportError:
    log.warning("openai module not installed - GPT service will be unavailable")

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
        log.debug(f"\n---prompt\n {prompt}\n---\n")
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
        log.debug(f"\n---reply\n {response}\n---\n")
        return response
    except Exception as e:
        log.error(f"Claude API error: {str(e)}")
        return f"Claude API error: {str(e)}"

@ai_retry_decorator
async def gpt(prompt: str, image_path: str) -> str:
    """Call GPT API with image and prompt."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        client = OpenAI(api_key=api_key)
        base64_image = encode_image(image_path)
        log.info("Calling GPT API")
        log.debug(f"\n---prompt\n {prompt}\n---\n")
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
        log.info("GPT API responded")
        log.debug(f"\n---reply\n {response}\n---\n")
        return response

    except Exception as e:
        log.error(f"GPT API error: {str(e)}")
        return f"GPT API error: {str(e)}"

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
        log.debug(f"\n---prompt\n {prompt}\n---\n")
        response = await model.generate_content_async(
            [uploaded_file, "\n\n", prompt],
            request_options={"timeout": 600},
            generation_config={"max_output_tokens": AI_MAX_TOKENS},
        )
        response = response.text
        log.info("Gemini API responded")
        log.debug(f"\n---reply\n {response}\n---\n")
        return response

    except Exception as e:
        log.error(f"Gemini API error: {str(e)}")
        return f"Gemini API error: {str(e)}"

AI_MODEL_MAP: Dict[str, callable] = {
    'claude': claude,
    'gpt': gpt,
    'gemini': gemini
}

async def async_identify_life(ai_model: str, image_path: str) -> Dict[str, str]:
    log.debug(f"Starting life identification with {ai_model} model")
    if not os.path.exists(image_path):
        log.error(f"Image file not found at {image_path}")
        return f"Error: Image file not found"
        
    log.debug("Loading life identification prompt and CSV data")
    prompt = "Identify any fish, invertebrates, and plants in this underwater image of an aquarium. Use the attached csv to confirm your identifications. Return only the life you can identify in the image. Return your answers in the same csv format as the attached csv.\n"
    with open(os.path.join(os.path.dirname(__file__), "ainotes", "life.csv")) as f:
        header = next(f)
        prompt += f"{header}\n"
        prompt += f.read()
    
    log.debug(f"Calling {ai_model} API for life identification")
    response = await AI_MODEL_MAP[ai_model](prompt, image_path)
    
    try:
        with get_db_session() as db:
            log.debug("Querying latest image from database")
            latest_image = db.query(DBImage).order_by(DBImage.timestamp.desc()).first()
            if not latest_image:
                log.error("No images found in database for analysis")
                raise ValueError("No images found in database")
            
            log.debug("Creating AI analysis record")
            analysis = DBAIAnalysis(
                id=datetime.now(timezone.utc).isoformat(),
                image_id=latest_image.id,
                ai_model=ai_model,
                analysis='identify_life',
                response=response,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(analysis)
            
            log.debug("Parsing CSV response to update life records")
            reader = csv.reader(response.splitlines())
            header_row = next(reader)
            if header_row != header.split(','):
                log.error(f"AI response header mismatch. Expected: {header}, Got: {','.join(header_row)}")
                raise ValueError("AI response header does not match expected format")
            
            updates = 0
            for row in reader:
                if len(row) >= 3:
                    log.debug(f"Processing life record: {row[0]}")
                    life = db.query(DBLife).filter(DBLife.emoji == row[0]).first()
                    if life:
                        life.last_seen_at = datetime.now(timezone.utc)
                        life.count = int(row[3]) if len(row) > 3 else 1
                        updates += 1
            
            log.info(f"Updated {updates} life records from {ai_model} analysis")
            return response
            
    except Exception as e:
        log.error(f"Database error in identify_life: {str(e)}", exc_info=True)
        return f"Database error: {str(e)}"

async def async_estimate_temperature(ai_model: str, image_path: str) -> Dict[str, str]:
    """Estimate temperature from image and update database."""
    prompt = "Estimate the temperature of the water in this underwater image of an aquarium. Use the red digital submersible thermometer visible in the image.\n"
    response = await AI_MODEL_MAP[ai_model](prompt, image_path)
    
    try:
        with get_db_session() as db:
            # Get latest image
            latest_image = db.query(DBImage).order_by(DBImage.timestamp.desc()).first()
            if not latest_image:
                raise ValueError("No images found in database")
            
            # Create AI analysis record
            analysis = DBAIAnalysis(
                id=datetime.now(timezone.utc).isoformat(),
                image_id=latest_image.id,
                ai_model=ai_model,
                analysis='estimate_temperature',
                response=response,
                timestamp=datetime.now(timezone.utc)
            )
            db.add(analysis)
            
            # Try to extract temperature value from response
            import re
            temp_match = re.search(r'(\d+\.?\d*)\s*[°℉F]', response)
            if temp_match:
                temp = float(temp_match.group(1))
                # Create reading record
                reading = DBReading(
                    id=datetime.now(timezone.utc).isoformat(),
                    temperature=temp,
                    image_id=latest_image.id,
                    timestamp=datetime.now(timezone.utc)
                )
                db.add(reading)
                log.info(f"Added temperature reading: {temp}°F from {ai_model}")
            
            return response
            
    except Exception as e:
        log.error(f"Database update error in estimate_temperature: {str(e)}")
        return f"Database error: {str(e)}"

AI_ANALYSES_MAP: Dict[str, callable] = {
    'identify_life': async_identify_life,
    'estimate_temperature': async_estimate_temperature,
}

async def async_inference(ai_models: List[str], analyses: List[str], image_path: str) -> Dict[str, str]:
    log.debug(f"Starting AI inference - models: {ai_models}, analyses: {analyses}")
    try:
        if not ENABLED_MODELS:
            log.error("No AI APIs enabled")
            raise ValueError("No AI apis enabled")
        
        tasks = []
        task_keys = []
        for ai_model in ai_models:
            if ai_model not in ENABLED_MODELS:
                log.error(f"Requested model {ai_model} not in enabled models: {ENABLED_MODELS}")
                raise ValueError(f"Model {ai_model} not enabled")
            for analysis in analyses:
                if analysis not in AI_ANALYSES_MAP:
                    log.error(f"Requested analysis {analysis} not found in available analyses: {list(AI_ANALYSES_MAP.keys())}")
                    raise ValueError(f"Analysis {analysis} not found in AI_ANALYSES_MAP")
                log.debug(f"Adding task: {ai_model}.{analysis}")
                tasks.append(AI_ANALYSES_MAP[analysis](ai_model, image_path))
                task_keys.append(f"{ai_model}.{analysis}")
        
        if not tasks:
            log.error("No tasks created - check enabled models and analyses")
            raise ValueError("No enabled models found in model map")
            
        log.debug(f"Executing {len(tasks)} inference tasks")
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        results = {
            key: resp if not isinstance(resp, Exception) else str(resp)
            for key, resp in zip(task_keys, responses)
        }
        
        log.debug("Inference results:")
        for key, result in results.items():
            if isinstance(result, Exception):
                log.error(f"{key} failed: {str(result)}")
            else:
                log.debug(f"{key} succeeded")
        
        return results
        
    except Exception as e:
        log.error(f"AI inference error: {str(e)}", exc_info=True)
        return {"error": f"AI inference failed: {str(e)}"}
