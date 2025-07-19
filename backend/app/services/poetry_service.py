"""
AI Poetry generation service using OpenAI
"""
import base64
import asyncio
from typing import Tuple, Optional
from pathlib import Path
import openai
from PIL import Image as PILImage

from app.core.config import settings


class PoetryService:
    """Service for generating poetry from images using OpenAI"""
    
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for poetry generation")
        
        openai.api_key = settings.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_poetry_from_image(
        self, 
        image_path: str, 
        style: str = "classic",
        language: str = "korean"
    ) -> Tuple[str, str]:
        """
        Generate poetry from image
        
        Args:
            image_path: Path to the image file
            style: Poetry style (classic, modern, haiku, free_verse)
            language: Poetry language (korean, english, japanese)
            
        Returns:
            Tuple of (title, poetry_content)
            
        Raises:
            Exception: If poetry generation fails
        """
        try:
            # Read and encode image
            image_base64 = self._encode_image(image_path)
            
            # Create appropriate prompt based on language and style
            prompt = self._create_poetry_prompt(style, language)
            
            # Call OpenAI API
            response = await self._call_openai_vision_api(image_base64, prompt)
            
            # Parse response to extract title and content
            title, content = self._parse_poetry_response(response, language)
            
            return title, content
            
        except Exception as e:
            raise Exception(f"Failed to generate poetry: {str(e)}")
    
    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        try:
            # Open and potentially resize image to reduce API costs
            with PILImage.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize if image is too large (max 1024x1024 for optimal API usage)
                max_size = 1024
                if img.width > max_size or img.height > max_size:
                    img.thumbnail((max_size, max_size), PILImage.Resampling.LANCZOS)
                
                # Save to bytes and encode
                import io
                byte_arr = io.BytesIO()
                img.save(byte_arr, format='JPEG', quality=85)
                return base64.b64encode(byte_arr.getvalue()).decode()
                
        except Exception as e:
            raise Exception(f"Failed to encode image: {str(e)}")
    
    def _create_poetry_prompt(self, style: str, language: str) -> str:
        """
        Create appropriate prompt for poetry generation
        
        Args:
            style: Poetry style
            language: Poetry language
            
        Returns:
            Formatted prompt string
        """
        prompts = {
            "korean": {
                "classic": """
이 이미지를 보고 아름다운 한국 고전시를 창작해주세요.
다음 형식으로 응답해주세요:

제목: [시의 제목]

[시의 내용]

요구사항:
- 한국의 전통적인 서정시 스타일
- 4-8행 정도의 적절한 길이
- 이미지의 감정과 분위기를 잘 표현
- 아름답고 서정적인 언어 사용
""",
                "modern": """
이 이미지를 보고 현대적인 한국어 자유시를 창작해주세요.
다음 형식으로 응답해주세요:

제목: [시의 제목]

[시의 내용]

요구사항:
- 현대적이고 자유로운 형식
- 이미지의 현대적 감각을 표현
- 일상적이면서도 깊이 있는 언어
- 6-10행 정도의 길이
""",
                "haiku": """
이 이미지를 보고 하이쿠(5-7-5 음성률) 형식의 한국어 시를 창작해주세요.
다음 형식으로 응답해주세요:

제목: [시의 제목]

[첫 번째 줄 - 5음성]
[두 번째 줄 - 7음성]  
[세 번째 줄 - 5음성]

요구사항:
- 정확한 5-7-5 음성률 준수
- 자연과 계절감을 중시
- 간결하고 함축적인 표현
""",
                "free_verse": """
이 이미지를 보고 자유로운 형식의 한국어 시를 창작해주세요.
다음 형식으로 응답해주세요:

제목: [시의 제목]

[시의 내용]

요구사항:
- 완전히 자유로운 형식과 리듬
- 실험적이고 창의적인 표현
- 이미지의 독특한 면을 부각
- 길이 제한 없음
"""
            },
            "english": {
                "classic": """
Looking at this image, please create a beautiful classical English poem.
Please respond in this format:

Title: [poem title]

[poem content]

Requirements:
- Traditional English poetry style
- 4-8 lines of appropriate length
- Express the emotion and atmosphere of the image well
- Use beautiful and lyrical language
""",
                "modern": """
Looking at this image, please create a modern English free verse poem.
Please respond in this format:

Title: [poem title]

[poem content]

Requirements:
- Modern and free format
- Express the contemporary sense of the image
- Everyday yet profound language
- About 6-10 lines
""",
                "haiku": """
Looking at this image, please create a haiku (5-7-5 syllable pattern) in English.
Please respond in this format:

Title: [poem title]

[First line - 5 syllables]
[Second line - 7 syllables]
[Third line - 5 syllables]

Requirements:
- Strict 5-7-5 syllable pattern
- Focus on nature and seasons
- Concise and implicit expression
""",
                "free_verse": """
Looking at this image, please create a free verse English poem.
Please respond in this format:

Title: [poem title]

[poem content]

Requirements:
- Completely free format and rhythm
- Experimental and creative expression
- Highlight unique aspects of the image
- No length restrictions
"""
            }
        }
        
        return prompts.get(language, prompts["korean"]).get(style, prompts[language]["classic"])
    
    async def _call_openai_vision_api(self, image_base64: str, prompt: str) -> str:
        """
        Call OpenAI Vision API
        
        Args:
            image_base64: Base64 encoded image
            prompt: Poetry generation prompt
            
        Returns:
            Generated poetry response
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_base64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")
    
    def _parse_poetry_response(self, response: str, language: str) -> Tuple[str, str]:
        """
        Parse OpenAI response to extract title and content
        
        Args:
            response: Raw OpenAI response
            language: Poetry language for fallback titles
            
        Returns:
            Tuple of (title, content)
        """
        try:
            lines = response.strip().split('\n')
            title = ""
            content = ""
            
            # Look for title pattern
            for i, line in enumerate(lines):
                line = line.strip()
                if line.startswith('제목:') or line.startswith('Title:'):
                    title = line.split(':', 1)[1].strip()
                    # Content is everything after the title line
                    content = '\n'.join(lines[i+1:]).strip()
                    break
            
            # If no title found, use first line as title and rest as content
            if not title and lines:
                title = lines[0].strip()
                content = '\n'.join(lines[1:]).strip() if len(lines) > 1 else lines[0].strip()
            
            # Fallback if parsing fails
            if not title:
                fallback_titles = {
                    "korean": "이미지에서 영감을 받은 시",
                    "english": "A Poem Inspired by an Image",
                    "japanese": "画像からインスピレーションを得た詩"
                }
                title = fallback_titles.get(language, fallback_titles["korean"])
            
            if not content:
                content = response.strip()
            
            return title, content
            
        except Exception:
            # If parsing completely fails, return the response as content
            fallback_titles = {
                "korean": "이미지 시",
                "english": "Image Poetry", 
                "japanese": "画像詩"
            }
            return (
                fallback_titles.get(language, fallback_titles["korean"]),
                response.strip()
            )
    
    async def generate_simple_poetry(self, description: str, language: str = "korean") -> Tuple[str, str]:
        """
        Generate simple poetry without image (for testing)
        
        Args:
            description: Text description to generate poetry from
            language: Poetry language
            
        Returns:
            Tuple of (title, content)
        """
        try:
            prompt = f"""
주어진 설명을 바탕으로 아름다운 한국어 시를 창작해주세요.

설명: {description}

다음 형식으로 응답해주세요:
제목: [시의 제목]

[시의 내용]

요구사항:
- 4-8행 정도의 적절한 길이
- 서정적이고 아름다운 언어
- 주어진 설명의 감정과 분위기를 잘 표현
"""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.7
            )
            
            result = response.choices[0].message.content
            return self._parse_poetry_response(result, language)
            
        except Exception as e:
            raise Exception(f"Failed to generate simple poetry: {str(e)}")