from openai import AsyncOpenAI
from src.config import settings

# Models known to support tool/function calling well
RECOMMENDED_MODELS = {
    "huggingface": ["Meta-Llama-3.3-70B-Instruct", "DeepSeek-R1-Distill-Llama-70B", "DeepSeek-R1", "Meta-Llama-3.1-8B-Instruct"],
    "openrouter": ["meta-llama/llama-3.3-70b-instruct", "qwen/qwen-2.5-72b-instruct"],
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
}


class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER
        
        # Determine the base URL and API key based on the provider
        if self.provider == "ollama":
            # Ollama runs locally and exposes an OpenAI-compatible API
            base_url = settings.OLLAMA_BASE_URL
            api_key = "ollama"  # Ollama doesn't require a real API key
            self.model = settings.OLLAMA_MODEL
            print(f"[LLM] Using Ollama (local) with model: {self.model}")
            print(f"[LLM] Recommended models for tool calling: {', '.join(RECOMMENDED_MODELS['ollama'])}")

        elif self.provider == "vllm":
            base_url = settings.VLLM_API_URL
            api_key = "EMPTY"
            self.model = settings.VLLM_MODEL
            print(f"[LLM] Using vLLM with model: {self.model}")


        elif self.provider == "openrouter":
            # OpenRouter: one API key, access to many open-source models
            base_url = "https://openrouter.ai/api/v1"
            api_key = settings.OPENROUTER_API_KEY
            self.model = settings.OPENROUTER_MODEL
            if not api_key:
                raise ValueError(
                    "OPENROUTER_API_KEY environment variable is required when LLM_PROVIDER is 'openrouter'.\n"
                    "Get a key at: https://openrouter.ai"
                )
            print(f"[LLM] Using OpenRouter with model: {self.model}")

        elif self.provider == "huggingface":
            # HuggingFace Inference API (free tier available)
            base_url = "https://router.huggingface.co/sambanova/v1"
            api_key = settings.HF_API_KEY
            self.model = settings.HF_MODEL
            if not api_key:
                raise ValueError(
                    "HF_API_KEY environment variable is required when LLM_PROVIDER is 'huggingface'.\n"
                    "Get a free token at: https://huggingface.co/settings/tokens"
                )
            print(f"[LLM] Using HuggingFace Inference with model: {self.model}")

        else:
            # OpenAI or any other OpenAI-compatible provider
            base_url = settings.API_BASE_URL
            api_key = settings.API_KEY
            self.model = settings.MODEL_NAME
            if not api_key:
                raise ValueError(
                    f"API_KEY environment variable is required when LLM_PROVIDER is '{self.provider}'."
                )
            print(f"[LLM] Using {self.provider} with model: {self.model}")

        # Initialize the AsyncOpenAI client
        # Works for all providers since they expose OpenAI-compatible APIs
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
    async def generate_response(self, messages, tools=None):
        """
        Sends messages to the LLM and returns the response.
        Supports passing tools/functions if the model supports tool calling.
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,  # Low temperature for more precise/analytical tasks
            }
            
            if tools:
                kwargs["tools"] = tools
                # Some providers work better with explicit tool_choice
                if self.provider == "ollama":
                    kwargs["tool_choice"] = "auto"
                
            response = await self.client.chat.completions.create(**kwargs)
            return response.choices[0].message
            
        except Exception as e:
            print(f"Error communicating with LLM: {e}")
            raise
