# llms/llm_provider.py

from typing import Literal
import os

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel
from groq import RateLimitError


def get_groq_llm_with_fallback(temperature: float = 0.7) -> BaseChatModel:
    """
    Returns a Groq Chat model with fallback logic on RateLimitError.
    Checks multiple models defined in env vars: GROQ_MODEL, GROQ_MODEL_V2, GROQ_MODEL_V3.
    """
    model_priority = [
        os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        os.getenv("GROQ_MODEL_V2", "llama-3.1-8b-instant"),
        os.getenv("GROQ_MODEL_V3", "gemma2-9b-it"),
    ]

    for model_name in model_priority:
        try:
            llm = ChatGroq(
                model=model_name,
                temperature=temperature,
                api_key=os.getenv("GROQ_API_KEY")
            )
            # Lightweight sanity check to test if model works
            llm.invoke("Say hello!")
            print(f"[LLM] Using Groq model: {model_name}")
            return llm
        except RateLimitError:
            print(f"[LLM] Rate limit hit for model: {model_name}. Trying fallback...")
        except Exception as e:
            print(f"[LLM] Failed to initialize model {model_name}: {e}")

    raise RuntimeError("All Groq models failed or are rate-limited.")


def get_llm(
    provider: Literal["openai", "groq", "ollama"] = "ollama",
    temperature: float = 0.7
) -> BaseChatModel:
    """
    Returns an LLM instance based on the selected provider.

    Supported providers: "ollama", "groq", "openai"
    """
    if provider == "openai":
        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )

    elif provider == "groq":
        return get_groq_llm_with_fallback(temperature=temperature)

    elif provider == "ollama":
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            temperature=temperature
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
