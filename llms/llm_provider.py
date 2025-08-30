# llms/llm_provider.py

from typing import Literal
import os

from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_ollama import ChatOllama
from langchain_core.language_models.chat_models import BaseChatModel


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
        return ChatGroq(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            temperature=temperature,
            api_key=os.getenv("GROQ_API_KEY")
        )
    
    elif provider == "ollama":
        return ChatOllama(
            model=os.getenv("OLLAMA_MODEL", "llama3"),
            base_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            temperature=temperature
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
