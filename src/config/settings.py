import os
from dotenv import load_dotenv

# Load .env at module import
load_dotenv(override=True)

class Settings:
    @property
    def GITHUB_TOKEN(self):
        return os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")

    @property
    def LLM_PROVIDER(self):
        return os.getenv("LLM_PROVIDER", "openai").lower()
    
    @property
    def OLLAMA_BASE_URL(self):
        return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        
    @property
    def OLLAMA_MODEL(self):
        return os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    
    @property
    def VLLM_API_URL(self):
        return os.getenv("VLLM_API_URL", "http://localhost:8000/v1")
        
    @property
    def VLLM_MODEL(self):
        return os.getenv("VLLM_MODEL", "meta-llama/Meta-Llama-3-8B-Instruct")
    
    
    @property
    def OPENROUTER_API_KEY(self):
        return os.getenv("OPENROUTER_API_KEY") or os.getenv("API_KEY")
        
    @property
    def OPENROUTER_MODEL(self):
        return os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
    
    @property
    def HF_API_KEY(self):
        return os.getenv("HF_API_KEY") or os.getenv("API_KEY")
        
    @property
    def HF_MODEL(self):
        return os.getenv("HF_MODEL", "Meta-Llama-3.3-70B-Instruct")
    
    @property
    def API_BASE_URL(self):
        return os.getenv("API_BASE_URL")
        
    @property
    def API_KEY(self):
        return os.getenv("API_KEY")
        
    @property
    def MODEL_NAME(self):
        return os.getenv("MODEL_NAME", "gpt-4o")

settings = Settings()
