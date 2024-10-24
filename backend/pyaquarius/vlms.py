import os
import base64
import logging
from typing import Dict
import asyncio
from openai import OpenAI
from anthropic import Anthropic

log = logging.getLogger(__name__)

def encode_image(image_path: str) -> str:
    """Encode image to base64 string."""
    if not os.path.exists(image_path):
        raise ValueError(f"Image file not found: {image_path}")
    
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to encode image: {str(e)}")

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
            max_tokens=1024,
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
        reply = response.content[0].text
        log.info("Claude API responded")
        log.debug(f"Response: {reply}")
        return reply
    except Exception as e:
        log.error(f"Claude API error: {str(e)}")
        return f"Claude API error: {str(e)}"

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

        # Make the API call to OpenAI
        response = await asyncio.to_thread(
            client.chat.completions.create,
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
        )
        reply = response.choices[0].message.content
        log.info("GPT-4o-mini API responded")
        log.debug(f"Response: {reply}")
        return reply

    except Exception as e:
        log.error(f"GPT-4o-mini API error: {str(e)}")
        return f"GPT-4o-mini API error: {str(e)}"

async def caption(image_path: str, prompt: str) -> Dict[str, str]:
    """Generate captions for an image using multiple models."""
    try:
        responses = await asyncio.gather(
            claude(prompt, image_path),
            gpt4o_mini(prompt, image_path),
            return_exceptions=True
        )
        return {
            "claude": responses[0] if not isinstance(responses[0], Exception) else str(responses[0]),
            "gpt4o-mini": responses[1] if not isinstance(responses[1], Exception) else str(responses[1])
        }
    except Exception as e:
        log.error(f"Caption error: {str(e)}")
        return {"error": f"Caption failed: {str(e)}"}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(caption("test.jpg", "Describe what you see in this image."))