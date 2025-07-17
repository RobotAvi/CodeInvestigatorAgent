import requests
import json
from typing import Dict, Any, List
from config import settings


class LocalLLMClient:
    def __init__(self, model: str = None):
        self.base_url = settings.local_llm_url
        self.model = model or settings.local_llm_model
        
    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> str:
        """Generate response from local LLM"""
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            **kwargs
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["response"]
        except Exception as e:
            print(f"Error calling local LLM: {e}")
            return f"Error: Unable to generate response from LLM: {str(e)}"
    
    def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Chat with local LLM using message history"""
        # Convert messages to Ollama format
        formatted_messages = []
        for msg in messages:
            if msg["role"] == "system":
                formatted_messages.append({"role": "system", "content": msg["content"]})
            elif msg["role"] == "user":
                formatted_messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                formatted_messages.append({"role": "assistant", "content": msg["content"]})
        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": False,
            **kwargs
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()["message"]["content"]
        except Exception as e:
            print(f"Error calling local LLM chat: {e}")
            return f"Error: Unable to chat with LLM: {str(e)}"
    
    def is_available(self) -> bool:
        """Check if local LLM is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_models(self) -> List[str]:
        """Get available models"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            return []
        except:
            return []