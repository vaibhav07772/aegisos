"""Universal LLM client for AegisOS (Groq only)"""
import os
import json
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, before_sleep_log,
)

load_dotenv()
logger = logging.getLogger(__name__)


def get_llm(model_name: str = None, temperature: float = 0.2,
            json_mode: bool = False, max_tokens: int = 2000):
    """
    Get Groq LLM instance.
    
    Args:
        model_name: Groq model ID (e.g., 'openai/gpt-oss-20b')
        temperature: 0-1
        json_mode: Force JSON output
        max_tokens: Output token limit
    """
    model_name = model_name or os.getenv("DEFAULT_MODEL", "openai/gpt-oss-20b")
    
    kwargs = {
        "model": model_name,
        "api_key": os.getenv("GROQ_API_KEY"),
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    if json_mode:
        kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}
    
    return ChatGroq(**kwargs)


@retry(
    retry=retry_if_exception_type(Exception),
    wait=wait_exponential(multiplier=2, min=5, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def safe_invoke(llm, messages):
    """LLM invoke with auto-retry"""
    return llm.invoke(messages)


def safe_json_invoke(llm, messages) -> dict:
    """Invoke and parse JSON response with fallback"""
    response = safe_invoke(llm, messages)
    raw = response.content.strip()
    
    # Strip markdown fences
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()
    
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Extract JSON from text
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end > start:
            return json.loads(raw[start:end + 1])
        raise