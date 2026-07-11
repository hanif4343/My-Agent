"""
প্রোভাইডার কনফিগারেশন।
নতুন provider যোগ করতে চাইলে শুধু এই লিস্টে একটা এন্ট্রি বাড়াও।
priority যত কম, তত আগে ট্রাই হবে।
"""

import os

PROVIDERS = [
    {
        "name": "gemini",
        "priority": 1,
        "kind": "gemini",  # gemini has its own REST schema
        "model": "gemini-2.5-flash",
        "api_key_env": "GEMINI_API_KEY",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
    },
    {
        "name": "groq",
        "priority": 2,
        "kind": "openai_compatible",
        "model": "openai/gpt-oss-20b",  # llama-3.3-70b-versatile deprecated (জুন ১৭, ২০২৬)
        "api_key_env": "GROQ_API_KEY",
        "base_url": "https://api.groq.com/openai/v1/chat/completions",
    },
    {
        "name": "cerebras",
        "priority": 3,
        "kind": "openai_compatible",
        "model": "gpt-oss-120b",  # llama-3.3-70b deprecated (ফেব্রুয়ারি ১৬, ২০২৬)
        "api_key_env": "CEREBRAS_API_KEY",
        "base_url": "https://api.cerebras.ai/v1/chat/completions",
    },
    {
        "name": "mistral",
        "priority": 4,
        "kind": "openai_compatible",
        "model": "mistral-small-latest",
        "api_key_env": "MISTRAL_API_KEY",
        "base_url": "https://api.mistral.ai/v1/chat/completions",
    },
    {
        "name": "nvidia",
        "priority": 5,
        "kind": "openai_compatible",
        "model": "meta/llama-3.3-70b-instruct",
        "api_key_env": "NVIDIA_API_KEY",
        "base_url": "https://integrate.api.nvidia.com/v1/chat/completions",
    },
    {
        "name": "sambanova",
        "priority": 6,
        "kind": "openai_compatible",
        "model": "Meta-Llama-3.3-70B-Instruct",
        "api_key_env": "SAMBANOVA_API_KEY",
        "base_url": "https://api.sambanova.ai/v1/chat/completions",
    },
    {
        "name": "openrouter",
        "priority": 7,
        "kind": "openai_compatible",
        "model": "meta-llama/llama-3.3-70b-instruct:free",
        "api_key_env": "OPENROUTER_API_KEY",
        "base_url": "https://openrouter.ai/api/v1/chat/completions",
    },
]

# শুধু সেই প্রোভাইডার active থাকবে যার env var সেট আছে (key present)
def active_providers():
    result = []
    for p in PROVIDERS:
        if os.environ.get(p["api_key_env"]):
            result.append(p)
    return sorted(result, key=lambda x: x["priority"])


MAX_RETRY_PER_TASK = 3          # একটা টাস্কের জন্য AI-fix loop সর্বোচ্চ কতবার
MAX_PROVIDER_FAILOVER = len(PROVIDERS)  # একবারের call-এ কতগুলো provider ট্রাই করবে
REQUEST_TIMEOUT_SECONDS = 60
