import os
import json
import logging
import asyncio
import hashlib
import time
import re
from datetime import datetime
from typing import Optional, Dict, Any, Union, List

import httpx
import aiohttp
from openai import OpenAI
from dotenv import load_dotenv

from extensions import cache
from utils import Constants

load_dotenv()

logger = logging.getLogger(__name__)


class AIConfig:
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    ZAI_API_KEY = os.getenv("ZAI_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

    OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
    ZAI_API_URL = "https://api.zai-api.com/v1/chat/completions"
    DEEPSEEK_API_URL = "https://api.deepseek.com/v1"


class AIService:
    BASE_RULES = """
## KESİN KURALLAR
### 1. YASAK TERİMLER (ASLA KULLANMA)
- Gezegen isimleri: Mars, Venüs, Satürn, Jüpiter, Merkür, Ay, Güneş, Uranüs, Neptün, Plüton
- Burç isimleri: Koç, Boğa, İkizler, Yengeç, Aslan, Başak, Terazi, Akrep, Yay, Oğlak, Kova, Balık
- Ev numaraları: 1. ev, 7. ev, 10. ev vb.
- Açı isimleri: kavuşum, karşıt, üçgen, kare, altmışlık, kuintil
- Teknik terimler: transit, progresyon, natal, ascendant, midheaven, düğüm, retrograd
### 2. DİL VE ÜSLUP
- Sade, anlaşılır Türkçe
- Doğrudan ve net ifadeler
- Mistik/ezoterik dil KULLANMA
- Kişiye adıyla hitap et, samimi ama profesyonel
"""

    def __init__(self):
        self.sync_client = None
        if AIConfig.DEEPSEEK_API_KEY:
            self.sync_client = OpenAI(
                api_key=AIConfig.DEEPSEEK_API_KEY, base_url=AIConfig.DEEPSEEK_API_URL
            )

    @staticmethod
    def remove_emojis(text: str) -> str:
        emoji_pattern = re.compile(
            "[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff\U0001f680-\U0001f6ff\U0001f700-\U0001f77f"
            "\U0001f780-\U0001f7ff\U0001f800-\U0001f8ff\U0001f900-\U0001f9ff\U0001fa00-\U0001fa6f"
            "\U0001fa70-\U0001faff\U00002702-\U000027b0\U000024c2-\U0001f251\U0001f1e0-\U0001f1ff"
            "\U00002600-\U000026ff\U00002700-\U000027bf\U0000fe00-\U0000fe0f\U0001f000-\U0001f02f"
            "\U0001f0a0-\U0001f0ff]+",
            flags=re.UNICODE,
        )
        cleaned = emoji_pattern.sub("", text)
        cleaned = re.sub(r" +", " ", cleaned)
        return "\n".join(line.strip() for line in cleaned.split("\n")).strip()

    async def call_deepseek_async(
        self, session: aiohttp.ClientSession, prompt: str
    ) -> dict:
        if not AIConfig.DEEPSEEK_API_KEY:
            return {"success": False, "error": "No DeepSeek API Key"}
        headers = {
            "Authorization": f"Bearer {AIConfig.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Sen dünyanın en iyi astroloğusun."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.3,
        }
        try:
            async with session.post(
                f"{AIConfig.DEEPSEEK_API_URL}/chat/completions",
                json=payload,
                headers=headers,
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "interpretation": self.remove_emojis(content),
                    }
                return {"success": False, "error": f"Status {resp.status}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_ai_interpretation(
        self, astro_data: dict, interpretation_type: str, user_name: str, **kwargs
    ) -> dict:
        # Fallback to sync wrapper of async for now to maintain consistency
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            self.get_ai_interpretation_async(
                astro_data, interpretation_type, user_name, **kwargs
            )
        )

    async def get_ai_interpretation_async(
        self, astro_data: dict, interpretation_type: str, user_name: str, **kwargs
    ) -> dict:
        prompt = f"User: {user_name}\nType: {interpretation_type}\nData: {json.dumps(astro_data, default=str)}\n{self.BASE_RULES}"

        async with aiohttp.ClientSession() as session:
            result = await self.call_deepseek_async(session, prompt)
            if result["success"]:
                return result
            # Add other fallbacks (Zai, OpenRouter) here
            return {"success": False, "error": "All AI providers failed"}


ai_service = AIService()


def get_ai_interpretation_engine(astro_data, interpretation_type, user_name, **kwargs):
    return ai_service.get_ai_interpretation(
        astro_data, interpretation_type, user_name, **kwargs
    )
