from openai import AsyncOpenAI
from app.core.config import get_settings
from app.core.logging import logger

settings = get_settings()


def get_async_llm_client() -> AsyncOpenAI:
    """Instantiate and return an AsyncOpenAI client configured for any OpenAI-compatible provider.
    
    Compatible with:
    - Groq (https://api.groq.com/openai/v1)
    - OpenRouter (https://openrouter.ai/api/v1)
    - DeepSeek (https://api.deepseek.com/v1)
    - Together AI (https://api.together.xyz/v1)
    - Local Ollama / vLLM (http://localhost:11434/v1)
    """
    base_url = settings.LLM_BASE_URL.strip()
    api_key = settings.LLM_API_KEY.strip() or "dummy-api-key"

    logger.debug(
        "Initializing OpenAI-compatible LLM client with base_url: {} and model: {}",
        base_url,
        settings.LLM_MODEL,
    )

    return AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
    )
