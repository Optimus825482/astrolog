"""
AI Interpretations - Async Version
===================================

Bu modül, AI API çağrılarını async olarak yapar.
aiohttp kullanarak blocking I/O'yu önler ve performansı artırır.

Kullanım:
    from ai_interpretations_async import generate_interpretation_async
    interpretation = await generate_interpretation_async(provider="natal", chart_data={...})
"""

import os
import logging
import asyncio
import json
from typing import Optional, Dict, Any
import aiohttp
from dotenv import load_dotenv

load_dotenv()

# Ayarları yükle fonksiyonu
def load_local_settings():
    settings_path = os.path.join(os.path.dirname(__file__), 'instance', 'settings.json')
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

local_settings = load_local_settings()

# API Keys
GOOGLE_API_KEY = local_settings.get("llm_api_key") or os.getenv("GOOGLE_API_KEY")
OPENROUTER_API_KEY = local_settings.get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY")
ZAI_API_KEY = local_settings.get("zai_api_key") or os.getenv("ZAI_API_KEY")
DEEPSEEK_API_KEY = local_settings.get("deepseek_api_key") or os.getenv("DEEPSEEK_API_KEY")

# API Endpoints
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
ZAI_API_URL = "https://api.zai-api.com/v1/chat/completions"
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

logger = logging.getLogger(__name__)


def remove_emojis(text: str) -> str:
    """
    Metinden tüm emoji karakterlerini temizler.
    Android TalkBack erişilebilirlik okuyucusu emoji'leri sesli okuduğu için
    AI yorumlarından emoji'leri kaldırıyoruz.
    """
    import re
    
    # Kapsamlı emoji regex pattern'i
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Yüz ifadeleri (emoticons)
        "\U0001F300-\U0001F5FF"  # Semboller & piktogramlar
        "\U0001F680-\U0001F6FF"  # Ulaşım & harita sembolleri
        "\U0001F700-\U0001F77F"  # Alchemical semboller
        "\U0001F780-\U0001F7FF"  # Geometrik şekiller extended
        "\U0001F800-\U0001F8FF"  # Supplemental arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental semboller & piktogramlar
        "\U0001FA00-\U0001FA6F"  # Chess semboller
        "\U0001FA70-\U0001FAFF"  # Semboller & piktogramlar extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed karakterler
        "\U0001F1E0-\U0001F1FF"  # Bayraklar (iOS)
        "\U00002600-\U000026FF"  # Misc semboller (güneş, ay, yıldız vb.)
        "\U00002700-\U000027BF"  # Dingbats
        "\U0000FE00-\U0000FE0F"  # Variation selectors
        "\U0001F000-\U0001F02F"  # Mahjong tiles
        "\U0001F0A0-\U0001F0FF"  # Playing cards
        "]+",
        flags=re.UNICODE
    )
    
    # Emoji'leri kaldır
    cleaned = emoji_pattern.sub('', text)
    
    # Ardışık boşlukları tek boşluğa indir
    cleaned = re.sub(r' +', ' ', cleaned)
    
    # Satır başındaki/sonundaki boşlukları temizle
    cleaned = '\n'.join(line.strip() for line in cleaned.split('\n'))
    
    return cleaned.strip()


# Prompts (ai_interpretations.py'den kopyalandı)
BIRTH_CHART_PROMPT = """
Sen uzman bir astroloğsun. Aşağıdaki doğum haritası verilerine göre kapsamlı bir yorum yaz.

**Danışan:** {user_name}

**Gezegen Konumları:**
{planet_positions}

**Yükselen:** {ascendant}

**Önemli Açılar:**
{aspects}

Lütfen bu haritayı Türkçe olarak, sevgi dolu ve bilgilendirici bir dille yorumla. 
Güçlü yönleri, zorlu açıları ve potansiyel büyüme alanlarını detaylandır.
"""

DAILY_ANALYSIS_PROMPT = """
Merhaba {user_name},

Bugün için astrolojik analiz aşağıdadır:

{data}

Lütfen bugünkü enerjileri, fırsatları ve dikkat edilmesi gereken konuları Türkçe olarak yorumla.
"""

DETAILED_ANALYSIS_PROMPT = """
Kapsamlı Astrolojik Analiz - {user_name}

Veriler:
{data}

Lütfen bu haritayı derinlemesine, Türkçe olarak analiz et. 
Gizli potansiyeller, yaşam amacı, ilişki dinamikleri ve kariyer yönlerini detaylandır.
"""

TRANSIT_ANALYSIS_PROMPT = """
Gezegen Transit Analizi - {user_name}

**Natal Gezegenler:**
{natal_planets}

**Transit Gezegenler:**
{transit_planets}

**Transit-Natal Açılar:**
{transit_aspects}

Lütfen transit etkilerini Türkçe olarak yorumla. 
Şu anki hayatında nasıl yansıyacak?
"""

CHAT_PROMPT = """
Önceki yorum: {original_interpretation}

Kullanıcı mesajı: {user_message}

Lütfen kullanıcının sorusunu önceki yorumu dikkate alarak Türkçe olarak yanıtla.
"""


async def call_deepseek_async(session: aiohttp.ClientSession, prompt: str) -> Optional[Dict[str, Any]]:
    """
    Doğrudan DeepSeek API için async çağrı yap.
    """
    if not DEEPSEEK_API_KEY:
        logger.error("DEEPSEEK_API_KEY not configured")
        return None
    
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Sen dünyanın en iyi astroloğusun. Teknik terim kullanmadan, sade ve anlaşılır bir dille yorum yaparsın."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4096
    }
    
    try:
        async with session.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=60)) as response:
            if response.status != 200:
                text = await response.text()
                logger.error(f"DeepSeek API error ({response.status}): {text}")
                return {"success": False, "error": f"DeepSeek API error: {response.status}"}
                
            data = await response.json()
            if "choices" in data and len(data["choices"]) > 0:
                interpretation = data["choices"][0]["message"]["content"]
                # Emoji'leri temizle (Android TalkBack erişilebilirlik için)
                interpretation = remove_emojis(interpretation)
                return {"success": True, "interpretation": interpretation}
            else:
                return {"success": False, "error": "Invalid DeepSeek response format"}
                
    except Exception as e:
        logger.error(f"DeepSeek async call failed: {e}")
        return {"success": False, "error": str(e)}


async def call_zai_async(session: aiohttp.ClientSession, prompt: str) -> Optional[Dict[str, Any]]:
    """
    Zai API (GLM-4.7) için async çağrı yap.
    Zai kütüphanesi henüz tam asenkron değilse aiohttp ile doğrudan çağrılır.
    """
    if not ZAI_API_KEY:
        logger.error("ZAI_API_KEY not configured")
        return None
    
    headers = {
        "Authorization": f"Bearer {ZAI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "glm-4.7",
        "messages": [
            {"role": "system", "content": "Sen dünyanın en iyi astroloğusun. Teknik terim kullanmadan, sade ve anlaşılır bir dille yorum yaparsın."},
            {"role": "user", "content": prompt}
        ],
    }
    
    try:
        # Not: Gerçek endpoint URL'sini Zai dokümantasyonuna göre güncellemek gerekebilir
        # Şimdilik standart OpenAI formatı varsayılıyor
        async with session.post("https://api.zai-api.com/v1/chat/completions", json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=45)) as response:
            if response.status != 200:
                text = await response.text()
                logger.error(f"Zai API error ({response.status}): {text}")
                return {"success": False, "error": f"Zai API error: {response.status}"}
                
            data = await response.json()
            if "choices" in data and len(data["choices"]) > 0:
                interpretation = data["choices"][0]["message"]["content"]
                # Emoji'leri temizle (Android TalkBack erişilebilirlik için)
                interpretation = remove_emojis(interpretation)
                return {"success": True, "interpretation": interpretation}
            else:
                return {"success": False, "error": "Invalid Zai response format"}
                
    except Exception as e:
        logger.error(f"Zai async call failed: {e}")
        return {"success": False, "error": str(e)}


# Hyperbolic functions removed


async def call_openrouter_async(session: aiohttp.ClientSession, prompt: str, model: str = "deepseek/deepseek-chat") -> Optional[Dict[str, Any]]:
    """
    OpenRouter API'ye async çağrı yap.
    
    Args:
        session: aiohttp ClientSession
        prompt: Prompt text
        model: Model name
        
    Returns:
        Response dictionary or None if error
    """
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY not configured")
        return None
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://astro-ai-predictor.com",
        "X-Title": "Astro AI Predictor",
    }
    
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4028,
    }
    
    try:
        async with session.post(OPENROUTER_API_URL, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
            response.raise_for_status()
            data = await response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                interpretation = data["choices"][0]["message"]["content"]
                # Emoji'leri temizle (Android TalkBack erişilebilirlik için)
                interpretation = remove_emojis(interpretation)
                return {"success": True, "interpretation": interpretation}
            else:
                logger.error("OpenRouter API response missing 'choices'")
                return {"success": False, "error": "Invalid response format"}
                
    except asyncio.TimeoutError:
        logger.error("OpenRouter API timeout")
        return {"success": False, "error": "Request timeout"}
    except aiohttp.ClientError as e:
        logger.error(f"OpenRouter API error: {e}")
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error calling OpenRouter: {e}")
        return {"success": False, "error": str(e)}


async def generate_interpretation_async(
    provider: str,
    chart_data: Dict[str, Any],
    custom_prompt: Optional[str] = None,
    session: Optional[aiohttp.ClientSession] = None
) -> Optional[Dict[str, Any]]:
    """
    AI yorumunu async olarak oluştur.
    
    Args:
        provider: Provider type (natal, daily, detailed, transit, birth_chart, etc.)
        chart_data: Astrology chart data
        custom_prompt: Custom prompt override
        session: aiohttp ClientSession (optional, will create if not provided)
        
    Returns:
        Dictionary with interpretation or error
    """
    # Session oluştur veya verileni kullan
    should_close = False
    if session is None:
        session = aiohttp.ClientSession()
        should_close = True
    
    try:
        user_name = chart_data.get("user_name", "Değerli Danışanım")
        data = chart_data
        
        # Prompt'u hazırla
        if custom_prompt:
            prompt = custom_prompt
        elif provider.endswith("_chat"):
            prompt = CHAT_PROMPT.format(
                original_interpretation=data.get("last_interpretation", "") if isinstance(data, dict) else "",
                user_message=data if isinstance(data, str) else data.get("message", "")
            )
        elif provider == "birth_chart":
            # Doğru key: natal_planet_positions (eski: planet_positions)
            positions = data.get("natal_planet_positions") or data.get("planet_positions", {})
            planet_positions_str = ""
            for planet, details in positions.items():
                if isinstance(details, dict) and 'degree' in details:
                    sign = details.get('sign', '?')
                    house = details.get('house', '')
                    retro = " (R)" if details.get('retrograde') else ""
                    house_str = f" - {house}. Ev" if house else ""
                    planet_positions_str += f"- {planet}: {details['degree']:.2f}° {sign}{house_str}{retro}\n"
            
            # Doğru key: natal_ascendant (eski: ascendant)
            asc_info = data.get("natal_ascendant") or data.get("ascendant", {})
            if isinstance(asc_info, dict) and asc_info.get('degree') is not None:
                ascendant_str = f"{asc_info.get('sign', '?')} {asc_info.get('degree', 0):.2f}°"
            else:
                ascendant_str = "Bilinmiyor"
            
            # Doğru key: natal_aspects (eski: aspects)
            aspects = data.get("natal_aspects") or data.get("aspects", [])
            aspects_str = ""
            for aspect in aspects[:20]:  # En önemli 20 açı
                if isinstance(aspect, dict):
                    aspects_str += f"- {aspect.get('planet1', '?')} {aspect.get('aspect_type', '?')} {aspect.get('planet2', '?')} (Orb: {aspect.get('orb', 0):.2f}°)\n"
            
            prompt = BIRTH_CHART_PROMPT.format(
                user_name=user_name,
                planet_positions=planet_positions_str or "Gezegen verisi yok.",
                ascendant=ascendant_str,
                aspects=aspects_str or "Açı verisi yok.",
            )
            logger.debug(f"Generated birth_chart prompt: {prompt[:200]}...")
            
        elif provider == "daily":
            prompt = DAILY_ANALYSIS_PROMPT.format(user_name=user_name, data=str(data))
            logger.debug(f"Generated daily prompt: {prompt[:200]}...")
            
        elif provider == "detailed":
            prompt = DETAILED_ANALYSIS_PROMPT.format(user_name=user_name, data=str(data))
            logger.debug(f"Generated detailed prompt: {prompt[:200]}...")
            
        elif provider == "transit":
            # Doğru key: natal_planet_positions
            natal_positions = data.get("natal_planet_positions") or data.get("planet_positions", {})
            natal_planets_str = ""
            for planet, details in natal_positions.items():
                if isinstance(details, dict) and 'degree' in details:
                    retro = " (R)" if details.get('retrograde') else ""
                    natal_planets_str += f"- {planet}: {details.get('degree', 0):.2f}° {details.get('sign', '?')} ({details.get('house', '?')}. Ev){retro}\n"
            
            # Transit pozisyonları
            transit_positions = data.get("transit_positions") or data.get("transit_planet_positions", {})
            transit_planets_str = ""
            for planet, details in transit_positions.items():
                if isinstance(details, dict):
                    deg = details.get('longitude') or details.get('degree', 0)
                    retro = " (R)" if details.get("retrograde", False) else ""
                    transit_planets_str += f"- {planet}: {deg:.2f}° {details.get('sign', '?')} ({details.get('house', '?')}. Ev){retro}\n"
            
            # Transit-Natal Açıları
            transit_aspects = data.get("transit_to_natal_aspects") or data.get("transit_natal_aspects", [])
            transit_aspects_str = ""
            for aspect in transit_aspects[:25]:
                if isinstance(aspect, dict):
                    p1 = aspect.get('transit_planet') or aspect.get('planet1') or aspect.get('planet', '?')
                    p2 = aspect.get('natal_planet') or aspect.get('planet2', '?')
                    asp_type = aspect.get('aspect') or aspect.get('aspect_type', '?')
                    transit_aspects_str += f"- Transit {p1} {asp_type} Natal {p2} (Orb: {aspect.get('orb', 0):.2f}°)\n"
            
            prompt = TRANSIT_ANALYSIS_PROMPT.format(
                user_name=user_name,
                natal_planets=natal_planets_str or "Natal gezegen verisi yok.",
                transit_planets=transit_planets_str or "Transit gezegen verisi yok.",
                transit_aspects=transit_aspects_str or "Transit-Natal açı verisi yok.",
            )
            logger.debug(f"Generated transit prompt: {prompt[:200]}...")
            
        else:
            logger.warning(f"Unknown provider '{provider}', using detailed prompt")
            prompt = DETAILED_ANALYSIS_PROMPT.format(user_name=user_name, data=str(data))
        
        # API çağrısını yap - Önce Zai (Erkan'ın tercihi), sonra Hyperbolic, en son OpenRouter
        logger.info("Zai (GLM-4.7) ile asenkron yorum oluşturuluyor...")
        result = await call_zai_async(session, prompt)
        
        if result and result.get("success"):
            return result
        
        # 3. DeepSeek (Doğrudan) Dene
        logger.info("DeepSeek (Doğrudan) ile asenkron yorum oluşturuluyor...")
        result = await call_deepseek_async(session, prompt)
        
        if result and result.get("success"):
            return result

        logger.warning("DeepSeek başarısız oldu, OpenRouter deneniyor...")
        
        logger.warning("Hyperbolic başarısız oldu, OpenRouter deneniyor...")
        result = await call_openrouter_async(session, prompt)
        
        if result and result.get("success"):
            return result
        
        # Her ikisi de başarısız oldu
        error_msg = "Tüm API'ler başarısız oldu"
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
        
    finally:
        if should_close:
            await session.close()


# Wrapper function for synchronous use
def generate_interpretation_sync_wrapper(provider: str, chart_data: Dict[str, Any], custom_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Async fonksiyonu için sync wrapper.
    Flask route'larından çağırmak için.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(
        generate_interpretation_async(provider, chart_data, custom_prompt)
    )


if __name__ == "__main__":
    # Test
    async def test():
        test_data = {
            "user_name": "Test",
            "planet_positions": {"Sun": {"degree": 10.5, "sign": "Koç"}},
            "ascendant": {"sign": "Boğa", "degree": 15.2},
            "aspects": []
        }
        result = await generate_interpretation_async("birth_chart", test_data)
        print(result)
    
    asyncio.run(test())
