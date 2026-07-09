"""
ProviderRouter: একাধিক ফ্রি AI provider-কে একটা কমন ইন্টারফেসের পেছনে লুকিয়ে রাখে।
একটা provider rate-limit (429) বা error দিলে পরেরটা ট্রাই করে।
এটাই মূল "কোনো একটা AI-এর উপর নির্ভরশীল না" থাকার জায়গা।
"""

import time
import requests

from . import config


class AllProvidersFailedError(Exception):
    pass


class ProviderRouter:
    def __init__(self):
        self.providers = config.active_providers()
        if not self.providers:
            raise RuntimeError(
                "কোনো প্রোভাইডারের API key পাওয়া যায়নি। "
                "GEMINI_API_KEY / GROQ_API_KEY / CEREBRAS_API_KEY / OPENROUTER_API_KEY "
                "এর অন্তত একটা env var সেট করো।"
            )

    def generate(self, system_prompt: str, user_prompt: str, log=print) -> dict:
        """
        সব active provider ক্রমান্বয়ে ট্রাই করে।
        সফল হলে {"text": ..., "provider": ...} রিটার্ন করে।
        সব fail করলে AllProvidersFailedError রেইজ করে।
        """
        last_error = None
        for p in self.providers:
            try:
                log(f"  → চেষ্টা করছি: {p['name']} ({p['model']})")
                if p["kind"] == "gemini":
                    text = self._call_gemini(p, system_prompt, user_prompt)
                else:
                    text = self._call_openai_compatible(p, system_prompt, user_prompt)
                log(f"  ✔ {p['name']} সফল")
                return {"text": text, "provider": p["name"]}
            except RateLimitError as e:
                log(f"  ⚠ {p['name']} rate-limited, পরের provider-এ যাচ্ছি")
                last_error = e
                continue
            except Exception as e:
                log(f"  ✖ {p['name']} ব্যর্থ: {e}")
                last_error = e
                continue

        raise AllProvidersFailedError(f"সব provider ব্যর্থ হয়েছে। শেষ error: {last_error}")

    # ---------- individual provider calls ----------

    def _call_openai_compatible(self, p, system_prompt, user_prompt) -> str:
        import os

        api_key = os.environ[p["api_key_env"]]
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": p["model"],
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
        }
        resp = requests.post(
            p["base_url"], headers=headers, json=payload,
            timeout=config.REQUEST_TIMEOUT_SECONDS,
        )
        if resp.status_code == 429:
            raise RateLimitError(f"{p['name']} rate limit hit")
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def _call_gemini(self, p, system_prompt, user_prompt) -> str:
        import os

        api_key = os.environ[p["api_key_env"]]
        url = f"{p['base_url']}/{p['model']}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": user_prompt}]}],
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "generationConfig": {"temperature": 0.2},
        }
        resp = requests.post(url, json=payload, timeout=config.REQUEST_TIMEOUT_SECONDS)
        if resp.status_code == 429:
            raise RateLimitError("gemini rate limit hit")
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


class RateLimitError(Exception):
    pass
