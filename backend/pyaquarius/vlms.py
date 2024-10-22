import os
import base64
import logging
import asyncio
import imghdr
from typing import Dict, List, Optional, Any, Callable
from abc import ABC, abstractmethod
import PIL.Image
from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
import replicate

log = logging.getLogger(__name__)

class VLMError(Exception):
    pass

class BaseVLM(ABC):
    def __init__(self):
        self.max_retries = 3
        self.retry_delay = 1
        self.supported_formats = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
        self.max_image_size = 20 * 1024 * 1024  # 20MB
        self._setup()
    
    @abstractmethod
    def _setup(self) -> None:
        pass
    
    @abstractmethod
    async def text(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def image(self, prompt: str, image_path: str, **kwargs) -> str:
        pass

    def validate_image(self, image_path: str) -> None:
        if not os.path.exists(image_path):
            raise VLMError(f"Image file not found: {image_path}")
        
        file_size = os.path.getsize(image_path)
        if file_size > self.max_image_size:
            raise VLMError(f"Image size ({file_size/1024/1024:.1f}MB) exceeds maximum allowed (20MB)")
        
        image_type = imghdr.what(image_path)
        if not image_type:
            raise VLMError(f"Could not determine image type for: {image_path}")
        
        mime_type = f"image/{image_type}"
        if mime_type not in self.supported_formats:
            raise VLMError(f"Unsupported image format: {mime_type}")

    def encode_image(self, image_path: str) -> str:
        self.validate_image(image_path)
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def process_with_retry(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any
    ) -> str:
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                log.warning(f"Error on attempt {attempt + 1}/{self.max_retries}: {e}")
                last_error = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                else:
                    raise VLMError(f"All retries failed: {str(e)}") from e
        
        raise last_error or VLMError("All retries failed")

class ClaudeVLM(BaseVLM):
    def _setup(self) -> None:
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise VLMError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = Anthropic(api_key=self.api_key)
        self.default_model = "claude-3-opus-20240229"

    async def text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> str:
        async def _make_request():
            response = await self.client.messages.create(
                messages=[{"role": "user", "content": prompt}],
                model=model or self.default_model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.content[0].text
        
        return await self.process_with_retry(_make_request)

    async def image(
        self,
        prompt: str,
        image_path: str,
        model: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> str:
        base64_image = self.encode_image(image_path)
        
        async def _make_request():
            response = await self.client.messages.create(
                model=model or self.default_model,
                max_tokens=max_tokens,
                temperature=temperature,
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
            return response.content[0].text
        
        return await self.process_with_retry(_make_request)

class OpenAIVLM(BaseVLM):
    def _setup(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise VLMError("OPENAI_API_KEY environment variable is not set")
        self.client = OpenAI(api_key=self.api_key)
        self.default_text_model = "gpt-4-1106-preview"
        self.default_vision_model = "gpt-4-vision-preview"

    async def text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> str:
        async def _make_request():
            response = await self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model or self.default_text_model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        
        return await self.process_with_retry(_make_request)

    async def image(
        self,
        prompt: str,
        image_path: str,
        model: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> str:
        base64_image = self.encode_image(image_path)
        
        async def _make_request():
            response = await self.client.chat.completions.create(
                model=model or self.default_vision_model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        
        return await self.process_with_retry(_make_request)

class GeminiVLM(BaseVLM):
    def _setup(self) -> None:
        self.api_key = os.getenv("GOOGLE_SDK_API_KEY")
        if not self.api_key:
            raise VLMError("GOOGLE_SDK_API_KEY environment variable is not set")
        genai.configure(api_key=self.api_key)
        self.default_text_model = "models/gemini-pro"
        self.default_vision_model = "models/gemini-pro-vision"

    async def text(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        async def _make_request():
            response = genai.GenerativeModel(
                model or self.default_text_model
            ).generate_content(prompt)
            return response.text
        
        return await self.process_with_retry(_make_request)

    async def image(
        self,
        prompt: str,
        image_path: str,
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        self.validate_image(image_path)
        
        async def _make_request():
            response = genai.GenerativeModel(
                model or self.default_vision_model
            ).generate_content([prompt, PIL.Image.open(image_path)])
            return response.text
        
        return await self.process_with_retry(_make_request)

class MistralVLM(BaseVLM):
    def _setup(self) -> None:
        self.default_text_model = "mistralai/mixtral-8x7b-instruct-v0.1"
        self.default_vision_model = "yorickvp/llava-v1.6-34b"
        self.model_versions = {
            "text": "cf18decbf51c27fed6bbdc3492312c1c903222a56e3fe9ca02d6cbe5198afc10",
            "vision": "41ecfbfb261e6c1adf3ad896c9066ca98346996d7c4045c5bc944a79d430f174"
        }

    async def text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> str:
        async def _make_request():
            output = replicate.run(
                f"{model or self.default_text_model}:{self.model_versions['text']}",
                input={
                    "prompt": prompt,
                    "max_new_tokens": max_tokens,
                    "temperature": temperature
                },
            )
            return "".join(output)
        
        return await self.process_with_retry(_make_request)

    async def image(
        self,
        prompt: str,
        image_path: str,
        model: Optional[str] = None,
        max_tokens: int = 256,
        temperature: float = 0.7
    ) -> str:
        base64_image = self.encode_image(image_path)
        
        async def _make_request():
            output = replicate.run(
                f"{model or self.default_vision_model}:{self.model_versions['vision']}",
                input={
                    "image": f"data:image/jpeg;base64,{base64_image}",
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature
                },
            )
            return "".join(output)
        
        return await self.process_with_retry(_make_request)

class VLMManager:
    def __init__(self):
        self.vlms = {
            "Claude": ClaudeVLM(),
            "OpenAI": OpenAIVLM(),
            "Gemini": GeminiVLM(),
            "Mistral": MistralVLM()
        }

    async def caption(
        self,
        image_path: str = "cover.png",
        prompt: str = "Describe the image",
    ) -> Dict[str, str]:
        tasks = []
        for name, vlm in self.vlms.items():
            task = asyncio.create_task(
                vlm.image(prompt, image_path),
                name=name
            )
            tasks.append(task)

        results = {}
        for task in tasks:
            try:
                result = await asyncio.wait_for(task, timeout=60.0)
                results[task.get_name()] = result
            except asyncio.TimeoutError:
                results[task.get_name()] = "API timeout"
            except Exception as e:
                results[task.get_name()] = f"API error: {str(e)}"
        
        return results

_manager: Optional[VLMManager] = None

def get_manager() -> VLMManager:
    global _manager
    if _manager is None:
        _manager = VLMManager()
    return _manager

async def caption(*args, **kwargs) -> Dict[str, str]:
    return await get_manager().caption(*args, **kwargs)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    asyncio.run(caption())