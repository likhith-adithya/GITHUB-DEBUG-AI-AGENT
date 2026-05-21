import os

from src.core.llm import RECOMMENDED_MODELS


def _get_available_providers() -> list:
    """Return only providers that have required credentials set."""
    checks = {
        "ollama": lambda: True,  # Local, no key needed
        "huggingface": lambda: bool(os.getenv("HF_API_KEY")),
        "openrouter": lambda: bool(os.getenv("OPENROUTER_API_KEY") or os.getenv("API_KEY")),
        "openai": lambda: bool(os.getenv("API_KEY")),
        "vllm": lambda: True,  # Self-hosted, no key needed
        "google": lambda: bool(os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")),
    }
    return [p for p in RECOMMENDED_MODELS if checks.get(p, lambda: False)()]


def select_llm_configuration():
    print("\n" + "=" * 60)
    print("  ⚙️ Configure AI Engine")
    print("=" * 60)

    providers = _get_available_providers()

    # 1. Select Provider
    print("Available Providers:")
    for i, p in enumerate(providers):
        print(f"  {i + 1}. {p}")
    print(f"  {len(providers) + 1}. default (use .env)")

    while True:
        try:
            choice = input("\nSelect provider number > ")
            choice_idx = int(choice) - 1
            if choice_idx == len(providers):
                return  # Use defaults
            if 0 <= choice_idx < len(providers):
                selected_provider = providers[choice_idx]
                break
        except ValueError:
            pass
        print("Invalid choice, please select a number.")

    os.environ["LLM_PROVIDER"] = selected_provider

    # 2. Select Model
    models = RECOMMENDED_MODELS[selected_provider]
    print(f"\nRecommended models for {selected_provider}:")
    for i, m in enumerate(models):
        print(f"  {i + 1}. {m}")
    print(f"  {len(models) + 1}. other (type manually)")

    while True:
        try:
            choice = input("\nSelect model number > ")
            choice_idx = int(choice) - 1
            if choice_idx == len(models):
                selected_model = input("Enter exactly model name > ")
                break
            if 0 <= choice_idx < len(models):
                if isinstance(models, dict):
                    selected_model = models.get(choice_idx)
                else:
                    selected_model = models[choice_idx]
                break
        except ValueError:
            pass
        print("Invalid choice, please select a number.")

    # Map back to environment variables Settings expects
    if selected_provider == "ollama":
        os.environ["OLLAMA_MODEL"] = selected_model
    elif selected_provider == "huggingface":
        os.environ["HF_MODEL"] = selected_model
    elif selected_provider == "openrouter":
        os.environ["OPENROUTER_MODEL"] = selected_model
    elif selected_provider == "openai":
        os.environ["MODEL_NAME"] = selected_model

    print(f"\nConfigured: {selected_provider} running {selected_model}")
