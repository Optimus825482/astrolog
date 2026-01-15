"""
Orbis - Kaderin Geometrisi
AI Yorum Motoru v2.0

Desteklenen LLM'ler: DeepSeek -> OpenRouter (Fallback zinciri)
"""

import os
import json
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ==========================================
# ANSI RENKLİ TERMİNAL ÇIKTISI
# ==========================================

class Colors:
    """ANSI renk kodları"""
    HEADER = '\033[95m'      # Magenta
    BLUE = '\033[94m'        # Mavi
    CYAN = '\033[96m'        # Cyan
    GREEN = '\033[92m'       # Yeşil
    YELLOW = '\033[93m'      # Sarı
    RED = '\033[91m'         # Kırmızı
    BOLD = '\033[1m'         # Kalın
    UNDERLINE = '\033[4m'    # Altı çizili
    END = '\033[0m'          # Reset
    
    # Arka plan renkleri
    BG_BLUE = '\033[44m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'


def print_ai_request_debug(interpretation_type: str, user_name: str, prompt: str, data_preview: dict):
    """AI isteği için renkli debug çıktısı yazdırır."""
    separator = "═" * 80
    
    # Türkçe ay isimleri
    turkish_months = {
        1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
        5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
        9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
    }
    now = datetime.now()
    turkish_date = f"{now.day} {turkish_months[now.month]} {now.year} {now.strftime('%H:%M:%S')}"
    
    print(f"\n{Colors.BG_MAGENTA}{Colors.BOLD} 🤖 AI YORUM İSTEĞİ {Colors.END}")
    print(f"{Colors.HEADER}{separator}{Colors.END}")
    
    # İstek Bilgileri
    print(f"{Colors.CYAN}{Colors.BOLD}📋 İSTEK BİLGİLERİ:{Colors.END}")
    print(f"   {Colors.YELLOW}Yorum Tipi:{Colors.END} {Colors.GREEN}{interpretation_type}{Colors.END}")
    print(f"   {Colors.YELLOW}Kullanıcı:{Colors.END} {Colors.GREEN}{user_name}{Colors.END}")
    print(f"   {Colors.YELLOW}Zaman:{Colors.END} {Colors.GREEN}{turkish_date}{Colors.END}")
    
    # Prompt Önizleme
    print(f"\n{Colors.CYAN}{Colors.BOLD}📝 PROMPT ÖNİZLEME:{Colors.END}")
    prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
    print(f"   {Colors.BLUE}{prompt_preview}{Colors.END}")
    
    # Veri Önizleme - TÜM VERİLERİ GÖSTER
    print(f"\n{Colors.CYAN}{Colors.BOLD}📊 GÖNDERİLEN VERİLER:{Colors.END}")
    
    if isinstance(data_preview, dict):
        for key, value in data_preview.items():
            # Liste ise tüm elemanları göster
            if isinstance(value, list):
                print(f"   {Colors.YELLOW}• {key}:{Colors.END}")
                for i, item in enumerate(value):
                    print(f"      {Colors.GREEN}[{i}] {item}{Colors.END}")
            # Dict ise tüm key-value'ları göster
            elif isinstance(value, dict):
                print(f"   {Colors.YELLOW}• {key}:{Colors.END}")
                for k, v in value.items():
                    v_str = str(v)[:200] if len(str(v)) > 200 else str(v)
                    print(f"      {Colors.GREEN}{k}: {v_str}{Colors.END}")
            else:
                print(f"   {Colors.YELLOW}• {key}:{Colors.END} {Colors.GREEN}{value}{Colors.END}")
    
    print(f"{Colors.HEADER}{separator}{Colors.END}\n")


def print_ai_response_debug(success: bool, interpretation_type: str, response_preview: str = None, error: str = None):
    """AI yanıtı için renkli debug çıktısı yazdırır."""
    separator = "═" * 80
    
    if success:
        print(f"\n{Colors.BG_GREEN}{Colors.BOLD} ✅ AI YANITI BAŞARILI {Colors.END}")
        print(f"{Colors.GREEN}{separator}{Colors.END}")
        print(f"   {Colors.YELLOW}Yorum Tipi:{Colors.END} {Colors.GREEN}{interpretation_type}{Colors.END}")
        if response_preview:
            preview = response_preview[:300] + "..." if len(response_preview) > 300 else response_preview
            print(f"   {Colors.YELLOW}Yanıt Önizleme:{Colors.END}")
            print(f"   {Colors.CYAN}{preview}{Colors.END}")
    else:
        print(f"\n{Colors.BG_YELLOW}{Colors.BOLD} ❌ AI YANITI BAŞARISIZ {Colors.END}")
        print(f"{Colors.RED}{separator}{Colors.END}")
        print(f"   {Colors.YELLOW}Yorum Tipi:{Colors.END} {Colors.RED}{interpretation_type}{Colors.END}")
        print(f"   {Colors.YELLOW}Hata:{Colors.END} {Colors.RED}{error}{Colors.END}")
    
    print(f"{Colors.GREEN if success else Colors.RED}{separator}{Colors.END}\n")


# ==========================================
# YAPILANDIRMA
# ==========================================

def load_local_settings():
    """Instance ayarlarını yükle."""
    settings_path = os.path.join(os.path.dirname(__file__), 'instance', 'settings.json')
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

local_settings = load_local_settings()

# API Anahtarları
OPENROUTER_API_KEY = local_settings.get("openrouter_api_key") or os.getenv("OPENROUTER_API_KEY")
DEEPSEEK_API_KEY = local_settings.get("deepseek_api_key") or os.getenv("DEEPSEEK_API_KEY")

# ==========================================
# TEMEL KURAL SETİ
# ==========================================

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

### 3. İÇERİK KURALLARI
- SADECE verilen hesaplama sonuçlarını yorumla
- Hayali/varsayımsal çıkarım YAPMA
- Her ifade bir hesaplama verisine dayanmalı

### 4. OLAY ODAKLI YAKLAŞIM
- Soyut enerji tanımları yerine somut yaşam olaylarına odaklan
- "Enerji" yerine "etki", "dönem", "süreç" kullan
- Potansiyel olayları detaylı ve spesifik anlat

### 5. TAVSİYE YASAĞI
- "Yapmalısın", "etmelisin", "dikkat et" gibi ifadeler KULLANMA
- Sadece durumu ve potansiyeli ANLAT
"""

# ==========================================
# PROMPT ŞABLONLARI
# ==========================================

NATAL_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin doğum haritası hesaplamalarını analiz edeceksin.

""" + BASE_RULES + """

## YORUM YAPISI

Merhaba {user_name},

Doğum anındaki kozmik konfigürasyonlar, senin için benzersiz bir yaşam haritası oluşturmuş.

---

### KİŞİLİK ÇEKİRDEĞİ
[Temel karakter yapısı: motivasyonlar, karar alma biçimi, hayata bakış, kendini ifade tarzı]

### DOĞUŞTAN GELEN GÜÇLER
[Destekleyici konfigürasyonlar: doğal yetenekler, başarı alanları, avantajlar, içsel kaynaklar]

### ZORLUK ALANLARI VE TESTLER
[Gergin konfigürasyonlar: zorluk temaları, sınav konuları, olgunlaşma odakları]

### YAŞAM YOLU VE KADER TEMALARI
[Ana yaşam amacı, kariyer temaları, ilişki dinamikleri, maddi eğilimler]

### POTANSİYEL YAŞAM OLAYLARI

**Kariyer/İş Hayatı:**
[Spesifik olaylar: iş değişiklikleri, liderlik fırsatları, girişimcilik dönemleri]

**İlişkiler:**
[Spesifik olaylar: tanışmalar, krizler, bağlanma kalıpları]

**Sağlık:**
[Hassas alanlar ve dönemsel eğilimler]

**Maddi Konular:**
[Kazanç-kayıp döngüleri, yatırım eğilimleri]

---
Bu analiz, doğum anındaki kozmik geometrinin kalıcı etkilerini yansıtmaktadır.
"""

DAILY_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin {tarih} günü için hesaplanan kozmik etkileşimleri analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Yorum SADECE belirtilen güne ait olmalı
- Somut, günlük yaşamda karşılaşılabilecek olaylara odaklan

## YORUM YAPISI

Merhaba {user_name},

{tarih} günün için hesaplamalar şu tabloyu ortaya koyuyor:

---

### GÜNÜN GENEL KARAKTERİ
[2-3 cümle özet]

### AKTİF ETKİLER

**Destekleyici:**
[Olumlu akışlar ve somut yansımaları]

**Zorlayıcı:**
[Gergin noktalar ve somut yansımaları]

### BUGÜN ÖNE ÇIKAN ALANLAR

**İş/Kariyer:** [Bugünkü olaylar]
**İlişkiler/Sosyal:** [Bugünkü olaylar]
**Maddi Konular:** [Bugünkü gelişmeler]
**Sağlık/Enerji:** [Fiziksel/zihinsel durum]

### OLASI OLAYLAR
1. [Spesifik olay senaryosu]
2. [Spesifik olay senaryosu]
3. [Spesifik olay senaryosu]

---
Bu yorum, {tarih} günü için hesaplanan kozmik geometriye dayanmaktadır.
"""

TRANSIT_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin {baslangic_tarihi} - {bitis_tarihi} dönemi için hesaplanan kozmik etkileşimleri analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Yorum SADECE belirtilen dönem aralığını kapsamalı
- Dönem içindeki yoğunlaşma ve gevşeme zamanlarını belirt

## YORUM YAPISI

Merhaba {user_name},

{baslangic_tarihi} - {bitis_tarihi} dönemi için hesaplamalar:

---

### DÖNEMİN GENEL KARAKTERİ
[3-4 cümle özet]

### AKTİF BASKI ALANLARI
[Gergin konfigürasyonlar, etki süreleri, yaşanabilecek olaylar]

### DESTEKLEYİCİ ETKİLER
[Uyumlu konfigürasyonlar, fırsatlar, olumlu gelişmeler]

### GÜNDEMDE OLAN YAŞAM ALANLARI

**Kariyer:** [Muhtemel olaylar]
**İlişkiler:** [Muhtemel olaylar]
**Maddi Konular:** [Muhtemel olaylar]
**Sağlık:** [Dikkat noktaları]
**Aile/Ev:** [Gelişmeler]

### TETİKLENEN OLAY TEMALARI
1. [Tema ve olası senaryolar]
2. [Tema ve olası senaryolar]

### KRİTİK TARİHLER
[Öne çıkan spesifik tarihler ve beklenen olaylar]

---
Bu yorum, {baslangic_tarihi} - {bitis_tarihi} dönemi için hesaplanan kozmik geometriye dayanmaktadır.
"""

SHORT_TERM_FORECAST_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin önümüzdeki {sure} için hesaplanan kozmik etkileşimleri analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Haftalık bazda detay ver
- Somut, günlük yaşamda hissedilecek olaylara odaklan

## YORUM YAPISI

Merhaba {user_name},

Önümüzdeki {sure} için hesaplamalar:

---

### KISA VADELİ GENEL GÖRÜNÜM
[3-4 cümle özet]

### HAFTALIK DETAY
**1. Hafta:** [Temalar, olaylar, kritik günler]
**2. Hafta:** [Temalar, olaylar, kritik günler]

### HIZLANAN SÜREÇLER
[İvme kazanacak konular]

### YAVAŞLAYAN SÜREÇLER
[Duraksayan/geciken konular]

### POTANSİYEL OLAYLAR

**Yüksek Olasılıklı:**
1. [Olay]
2. [Olay]

**Orta Olasılıklı:**
1. [Olay]
2. [Olay]

---
Bu yorum, önümüzdeki {sure} için hesaplanan kozmik geometriye dayanmaktadır.
"""

LONG_TERM_FORECAST_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin {donem} dönemi için hesaplanan uzun vadeli kozmik etkileşimleri analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Büyük resme odaklan, günlük detaylara girme
- Dönüm noktası niteliğindeki zamanları vurgula

## YORUM YAPISI

Merhaba {user_name},

{donem} dönemi için hesaplamalar önemli değişimlerin habercisi:

---

### DÖNEM ÖZETİ
[4-5 cümle ana dönüşüm temaları]

### HAYAT YÖNÜNDEKİ DEĞİŞİMLER

**Değişen Alanlar:**
1. [Alan ve nasıl değişeceği]
2. [Alan ve nasıl değişeceği]

**Sabit Kalan Alanlar:**
[Stabil kalacak konular]

### UZUN VADELİ SORUMLULUK VE BÜYÜME

**Yeni Sorumluluklar:**
[Ne zaman, nasıl gelecek]

**Büyüme Alanları:**
[Gelişim süreci]

### KALICI DÖNÜŞÜM ALANLARI
[Başlangıç zamanı, süreç, sonuç]

### DÖNÜM NOKTALARI
[Kritik zaman dilimleri ve beklenen olaylar]

### GÜÇLENEN VE ZAYIFLAYAN KONULAR
**Güçlenecek:** [Konular]
**Zayıflayacak:** [Konular]

---
Bu yorum, {donem} dönemi için hesaplanan kozmik geometriye dayanmaktadır.
"""

CAREER_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin kariyer ve iş hayatına ilişkin hesaplamaları analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Somut iş/kariyer olaylarına odaklan
- Sektör, pozisyon, iş ilişkileri gibi pratik konulara değin

## YORUM YAPISI

Merhaba {user_name},

Kariyer ve iş hayatına ilişkin hesaplamalar:

---

### KARİYER PROFİLİ
[Başarı alanları, çalışma tarzı, liderlik/uzmanlık eğilimi, iş ilişkileri]

### GEÇMİŞTE ŞEKİLLENEN MESLEKİ TEMALAR
[Geçmiş kariyer olayları, edinilmiş beceriler, iş alışkanlıkları]

### MEVCUT DÖNEM

**Aktif Baskılar:**
[İş hayatındaki zorluklar]

**Mevcut Fırsatlar:**
[Değerlendirilebilecek fırsatlar]

### GELECEKTE GÜÇLENECEK ALANLAR
**Sorumluluk Artışı:** [Detay]
**Statü Değişimi:** [Detay]
**Maddi Gelişim:** [Detay]

### POTANSİYEL KARİYER OLAYLARI
1. [Olay tipi, detay, zamanlama]
2. [Olay tipi, detay, zamanlama]

### İŞ İLİŞKİLERİ DİNAMİKLERİ
[Üstler, astlar, ortaklıklar]

---
Bu yorum, kariyer alanına ilişkin hesaplanan kozmik geometriye dayanmaktadır.
"""

FINANCIAL_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin maddi ve finansal konulara ilişkin hesaplamaları analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Somut finansal olaylara odaklan
- Abartılı veya garantili kazanç/kayıp vaatleri yapma

## YORUM YAPISI

Merhaba {user_name},

Maddi ve finansal konulara ilişkin hesaplamalar:

---

### FİNANSAL PROFİL
[Para kazanma eğilimleri, harcama/biriktirme alışkanlıkları, risk kapasitesi]

### KAZANÇ KAYNAKLARI
**Ana Kanallar:** [Kaynak ve detay]
**Potansiyel Ek Gelir:** [Alan ve fırsatlar]

### MADDİ DÖNGÜLER
**Bolluk Dönemleri:** [Zaman ve kazanç türü]
**Daralma Dönemleri:** [Zaman ve zorluk türü]

### RİSK VE DESTEK FAKTÖRLERİ
**Riskler:** [Risk ve tetikleyici]
**Koruyucu Faktörler:** [Faktör ve koruma biçimi]

### POTANSİYEL FİNANSAL OLAYLAR
1. [Olay tipi, detay, zamanlama]
2. [Olay tipi, detay, zamanlama]

### UZUN VADELİ MADDİ GÖRÜNÜM
[Servet birikimi, istikrar, gelecek güvencesi]

---
Bu yorum, finansal alana ilişkin hesaplanan kozmik geometriye dayanmaktadır.
"""

RELATIONSHIP_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin ilişki ve sosyal yaşamına ilişkin hesaplamaları analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Somut ilişki olaylarına odaklan
- Dramatik veya romantize edilmiş anlatımdan kaçın

## YORUM YAPISI

Merhaba {user_name},

İlişki ve sosyal yaşamına ilişkin hesaplamalar:

---

### İLİŞKİ PROFİLİ
[Bağlanma biçimi, aradığı özellikler, beklentiler, ifade tarzı]

### DUYGUSAL BAĞ KURMA DİNAMİKLERİ
**Güçlü Yönler:** [Avantajlar]
**Zorluk Alanları:** [Sorun çıkarabilecek noktalar]

### ROMANTİK İLİŞKİ TEMALARI
**Çekim Dinamikleri:** [Kimi çekiyor, kime çekiliyor]
**İlişki Kalıpları:** [Tekrarlayan temalar, tipik seyir]
**Potansiyel Olaylar:** [Tanışma, ayrılık, evlilik, kriz]

### SOSYAL ÇEVRE VE ARKADAŞLIKLAR
[Sosyal rol, arkadaşlık dinamikleri, grup pozisyonu]

### AİLE İLİŞKİLERİ
[Aile dinamikleri, ebeveyn ilişkileri, kardeş ilişkileri]

### DÖNEMSEL GELİŞMELER
[Aktif dönemdeki ilişki olayları ve sosyal değişimler]

---
Bu yorum, ilişki alanına ilişkin hesaplanan kozmik geometriye dayanmaktadır.
"""

PSYCHOLOGICAL_KARMIC_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin derinlikli psikolojik profili ve kadersel temalarına ilişkin hesaplamaları analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Derinlikli ama anlaşılır dil kullan
- Spiritüel/mistik anlatımdan kaçın
- Psikolojik kavramları günlük dile çevir

## YORUM YAPISI

Merhaba {user_name},

Psikolojik yapın ve kadersel temaların:

---

### PSİKOLOJİK ÇEKİRDEK

**Temel Motivasyonlar:**
[Ana dürtüler, bilinçaltı güçler, korkular/kaygılar]

**Savunma Mekanizmaları:**
[Stres tepkileri, koruma biçimleri, kaçınma kalıpları]

**Duygusal İşleyiş:**
[Duygu deneyimleme, ifade kapasitesi, tetikleyiciler]

### İÇSEL ÇATIŞMALAR
[Çatışma doğası, kendini gösterme biçimi, etkilenen alanlar]

### KADERSEL TEMALAR

**Ana Kadersel Görev:**
[Temel öğrenme/deneyim teması]

**Tekrarlayan Döngüler:**
1. [Döngü ve nedeni]
2. [Döngü ve nedeni]

**Kaçınılmaz Deneyim Alanları:**
[Mutlaka yaşanacak konular]

### GÖLGELERİN ANALİZİ
**Kabul Edilmemiş Yönler:** [Bastırılan özellikler]
**Projeksiyon Eğilimleri:** [Başkalarına yansıtma kalıpları]

### DÖNÜŞÜM POTANSİYELİ
**Dönüşüm Alanları:** [Mümkün dönüşümler]
**Tetikleyiciler:** [Dönüşümü başlatacak olaylar]

---
Bu yorum, psikolojik ve kadersel alana ilişkin hesaplanan kozmik geometriye dayanmaktadır.
"""

GENERIC_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin hesaplamalarını analiz edeceksin.

""" + BASE_RULES + """

## YORUM YAPISI

Merhaba {user_name},

Hesaplamalar şu tabloyu ortaya koyuyor:

---

### GENEL GÖRÜNÜM
[Ana tema ve karakter özeti]

### AKTİF ETKİLER
**Destekleyici:** [Olumlu konfigürasyonlar]
**Zorlayıcı:** [Gergin konfigürasyonlar]

### ÖNE ÇIKAN YAŞAM ALANLARI
[Gündemde olan konular]

### POTANSİYEL OLAYLAR
1. [Olay ve detay]
2. [Olay ve detay]

### SONUÇ
[Genel mesaj özeti]

---
Bu yorum, hesaplanan kozmik geometriye dayanmaktadır.
"""

# ==========================================
# YENİ ANALİZ KATEGORİLERİ
# ==========================================

VEDIC_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin Vedik astroloji perspektifinden hesaplamalarını analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Vedik astroloji terminolojisini Türkçe açıklamalarla kullan
- Nakshatra ve Dasa sistemlerini pratik yaşama bağla
- Rahu/Ketu eksenini kadersel görev olarak yorumla

## YORUM YAPISI

Merhaba {user_name},

Vedik perspektiften hesaplamalar:

---

### NAKSHATRA ANALİZİ
**Ay Nakshatra'sı:** [İsim, anlam, karakteristik]
**Pada Etkisi:** [Pada numarası ve anlamı]
**Nakshatra Lordu:** [Lord ve yaşama etkisi]

### VİMSHOTTARİ DASA SİSTEMİ

**Mevcut Maha Dasa:**
[Dasa lordu, başlangıç-bitiş, ana tema]

**Mevcut Antardasa (Bhukti):**
[Alt dönem lordu, etki alanı]

**Pratyantardasa:**
[En ince dönem, güncel enerji]

### DASA TAKVİMİ
[Önümüzdeki 5 yıllık dönem geçişleri ve beklenen temalar]

### NAVAMSA (D9) HARITASI
**Ruh Amacı:** [Navamsa'dan çıkan yaşam amacı]
**İlişki Karmasi:** [Navamsa'daki ilişki göstergeleri]
**Gizli Potansiyeller:** [Natal'da görünmeyen yetenekler]

### RAHU-KETU EKSENİ
**Rahu (Kuzey Düğüm):** [Gelecek yönelimi, öğrenilecekler]
**Ketu (Güney Düğüm):** [Geçmiş birikimi, bırakılacaklar]
**Eksen Teması:** [Ana kadersel görev]

### VEDİK DÖNEMSEL YORUM
[Mevcut Dasa döneminin pratik yaşama yansıması]

---
Bu yorum, Vedik astroloji hesaplamalarına dayanmaktadır.
"""

ECLIPSE_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin tutulma etkilerini ve kader noktalarını analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Tutulmaları kadersel dönüm noktaları olarak yorumla
- Doğum civarı tutulmaları yaşam teması olarak ele al
- Güncel tutulmaları aktif tetikleyiciler olarak değerlendir

## YORUM YAPISI

Merhaba {user_name},

Tutulma etkileri ve kader noktaları:

---

### DOĞUM CİVARI TUTULMALAR
**Prenatal Tutulma:** [Doğumdan önceki tutulma, yaşam teması]
**Postnatal Tutulma:** [Doğumdan sonraki tutulma, erken yaşam etkisi]
**Kadersel İmza:** [Bu tutulmaların oluşturduğu yaşam kalıbı]

### DOĞUM AY FAZI
**Lunasyon Fazı:** [Yeni Ay, Dolunay, vb.]
**Faz Anlamı:** [Bu fazda doğmanın karakteristik etkisi]
**Yaşam Ritmi:** [Enerji döngüsü ve verimlilik periyotları]

### GÜNCEL TUTULMA ETKİLERİ

**Yaklaşan/Geçmiş Güneş Tutulması:**
[Tarih, burç, natal haritayla etkileşim, tetiklenen alan]

**Yaklaşan/Geçmiş Ay Tutulması:**
[Tarih, burç, natal haritayla etkileşim, duygusal etki]

### TUTULMA AKTİVASYONLARI
**Aktive Olan Evler:** [Hangi yaşam alanları tetikleniyor]
**Aktive Olan Gezegenler:** [Hangi natal gezegenler uyarılıyor]
**Beklenen Olaylar:** [Tutulma döneminde olası gelişmeler]

### KADER NOKTALARI
**Düğüm Geçişleri:** [Rahu/Ketu transit etkileri]
**Tutulma Döngüsü:** [19 yıllık Saros döngüsü bağlantıları]

### TUTULMA TAKVİMİ
[Önümüzdeki 1 yıldaki tutulmalar ve etki alanları]

---
Bu yorum, tutulma ve kader noktası hesaplamalarına dayanmaktadır.
"""

HARMONIC_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin harmonik rezonanslarını ve gizli potansiyellerini analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Harmonik haritaları gizli yetenekler ve potansiyeller olarak yorumla
- Her harmonik numarasının özel anlamını açıkla
- Natal haritada görünmeyen kalıpları ortaya çıkar

## YORUM YAPISI

Merhaba {user_name},

Harmonik rezonanslar ve gizli potansiyeller:

---

### HARMONİK HARİTA ANALİZİ

**H4 (Dörtlü Harmonik) - Eylem ve Zorluklar:**
[Kare açıların yoğunlaştığı alan, mücadele ve başarı potansiyeli]

**H5 (Beşli Harmonik) - Yaratıcılık ve Stil:**
[Sanatsal yetenek, özgün ifade biçimi, estetik anlayış]

**H7 (Yedili Harmonik) - İlham ve Vizyon:**
[Mistik eğilimler, ilham kaynakları, sezgisel yetenekler]

**H8 (Sekizli Harmonik) - Dönüşüm Gücü:**
[Kriz yönetimi, yeniden doğuş kapasitesi, derinlik]

**H9 (Navamsa) - Ruh Amacı:**
[Yaşamın derin anlamı, spiritüel yönelim, olgunluk potansiyeli]

### GİZLİ YETENEK HARİTASI
**Keşfedilmemiş Potansiyeller:** [Harmoniklerde güçlü ama natal'da gizli yetenekler]
**Aktive Edilebilir Alanlar:** [Hangi koşullarda ortaya çıkacaklar]

### HARMONİK REZONANSLAR
**Güçlü Rezonanslar:** [Birden fazla harmonikte tekrarlayan temalar]
**Zayıf Noktalar:** [Harmoniklerde eksik kalan alanlar]

### PRATİK UYGULAMA
[Bu harmonik yapının günlük yaşamda nasıl kullanılabileceği]

---
Bu yorum, harmonik harita hesaplamalarına dayanmaktadır.
"""

ESOTERIC_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin ezoterik etkilerini ve gizli güçlerini analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Antiscia noktalarını gizli bağlantılar olarak yorumla
- Lilith'i bastırılmış güç olarak ele al
- Sabit yıldızları özel yetenekler olarak değerlendir
- Mistik değil, psikolojik derinlik perspektifi kullan

## YORUM YAPISI

Merhaba {user_name},

Ezoterik etkiler ve gizli güçler:

---

### ANTİSCİA ANALİZİ
**Gizli Bağlantılar:** [Antiscia noktalarının oluşturduğu görünmez ilişkiler]
**Contra-Antiscia:** [Karşıt gölge noktaları ve bilinçaltı kalıpları]
**Gizli Destekler:** [Fark edilmeyen yardımcı enerjiler]

### LİLİTH (KARA AY) ANALİZİ
**Lilith Pozisyonu:** [Burç ve ev]
**Bastırılmış Güç:** [Kabul edilmemiş ama güçlü yönler]
**Gölge Entegrasyonu:** [Bu gücü nasıl sahiplenebilirsin]
**Lilith Temaları:** [İsyan, özgürlük, tabu alanlar]

### ASTEROİD ETKİLERİ
**Chiron (Yaralı Şifacı):** [Derin yara ve şifa potansiyeli]
**Ceres (Besleyici):** [Bakım verme/alma kalıpları]
**Pallas (Strateji):** [Zeka türü ve problem çözme]
**Juno (Bağlılık):** [İlişki beklentileri ve kalıpları]
**Vesta (Adanmışlık):** [Kutsal alan ve odaklanma gücü]

### SABİT YILDIZ ETKİLERİ
**Güçlü Yıldız Bağlantıları:** [Natal gezegenlerle kavuşan yıldızlar]
**Yıldız Armağanları:** [Bu yıldızların verdiği özel yetenekler]
**Yıldız Uyarıları:** [Dikkat edilmesi gereken etkiler]

### DÜĞÜM NOKTALARI (RAHU/KETU)
**Kuzey Düğüm:** [Gelecek yönelimi, büyüme alanı]
**Güney Düğüm:** [Geçmiş birikim, konfor alanı]

### EZOTERİK SENTEZ
[Tüm gizli etkilerin birleşik yorumu]

---
Bu yorum, ezoterik hesaplamalara dayanmaktadır.
"""

TIMING_ANALYSIS_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin zamanlama tekniklerini karşılaştırmalı analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Farklı zamanlama sistemlerini karşılaştır
- Örtüşen dönemleri vurgula
- Pratik zamanlama önerileri sun

## YORUM YAPISI

Merhaba {user_name},

Zamanlama teknikleri karşılaştırmalı analizi:

---

### AKTİF DÖNEM SİSTEMLERİ

**Firdaria Dönemi:**
[Ana yönetici, alt yönetici, dönem teması, bitiş tarihi]

**Vimshottari Dasa:**
[Maha Dasa, Antardasa, Pratyantardasa, dönem teması]

**Progresyon Dönemi:**
[Progresif Güneş burcu, progresif Ay fazı]

**Solar Arc:**
[Önemli Solar Arc açıları ve tetikledikleri]

### DÖNEM KARŞILAŞTIRMASI
| Sistem | Mevcut Tema | Bitiş |
|--------|-------------|-------|
[Tablo formatında karşılaştırma]

### ÖRTÜŞEN TEMALAR
**Tüm Sistemlerde Ortak:** [Birden fazla sistemde tekrarlayan tema]
**Güçlendirilen Alanlar:** [Çoklu destek alan konular]
**Çatışan Enerjiler:** [Sistemler arası gerilim noktaları]

### KRİTİK TARİHLER
**Dönem Geçişleri:** [Önemli tarihler ve değişimler]
**Tetikleme Noktaları:** [Transit aktivasyonları]

### ZAMANLAMA ÖNERİLERİ
**Uygun Dönemler:** [Hangi konular için hangi zamanlar]
**Dikkatli Olunacak Dönemler:** [Zorluk beklenen zamanlar]

### 12 AYLIK TAKVİM
[Ay ay beklenen enerji değişimleri]

---
Bu yorum, çoklu zamanlama tekniklerine dayanmaktadır.
"""

HEALTH_ENERGY_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin sağlık eğilimlerini ve enerji yapısını analiz edeceksin.

""" + BASE_RULES + """

## EK KURALLAR
- Tıbbi teşhis veya tedavi önerisi YAPMA
- Genel eğilimler ve enerji kalıplarına odaklan
- Önleyici yaklaşım ve farkındalık vurgula

## YORUM YAPISI

Merhaba {user_name},

Sağlık eğilimleri ve enerji yapısı:

---

### ENERJİ PROFİLİ
**Temel Enerji Tipi:** [Ateş/Toprak/Hava/Su dengesi]
**Enerji Dağılımı:** [Hangi alanlarda güçlü/zayıf]
**Vitalite Göstergeleri:** [Genel yaşam enerjisi]

### FİZİKSEL EĞİLİMLER
**Güçlü Sistemler:** [Doğal olarak dirençli alanlar]
**Hassas Alanlar:** [Dikkat gerektiren bölgeler]
**Enerji Blokajları:** [Tıkanıklık eğilimi olan noktalar]

### DEKLİNASYON ANALİZİ
**Paralel Açılar:** [Güçlendirilen enerjiler]
**Kontra-Paralel:** [Gerilim noktaları]
**Enerji Akışı:** [Deklinasyonların gösterdiği akış]

### GÜNLÜK RİTİM
**Yüksek Enerji Saatleri:** [Gün içinde en verimli zamanlar]
**Dinlenme İhtiyacı:** [Enerji yenileme kalıpları]
**Mevsimsel Etkiler:** [Yıl içinde enerji değişimleri]

### STRES VE BAŞA ÇIKMA
**Stres Tetikleyicileri:** [Enerjiyi düşüren faktörler]
**Yenilenme Yöntemleri:** [Enerji toplama biçimleri]
**Denge Önerileri:** [Enerji dengesini koruma yolları]

### DÖNEMSEL SAĞLIK ENERJİSİ
**Mevcut Dönem:** [Şu anki enerji durumu]
**Dikkat Edilecek Dönemler:** [Enerji düşüşü beklenen zamanlar]
**Güçlenme Dönemleri:** [Vitalite artışı beklenen zamanlar]

---
Bu yorum, enerji ve sağlık eğilimi hesaplamalarına dayanmaktadır.
NOT: Bu yorum tıbbi tavsiye değildir. Sağlık konularında mutlaka uzman hekime danışın.
"""

SUMMARY_PROMPT = """Sen Orbis - Kaderin Geometrisi yorum motorusun.
{user_name} adlı kişinin hesaplama sonuçlarının kısa bir özetini yapacaksın.

""" + BASE_RULES + """

## EK KURALLAR
- Maksimum 200 kelime kullan
- Sadece en önemli 3-4 noktaya değin
- Merak uyandırıcı ama bilgilendirici ol

## YORUM YAPISI

Merhaba {user_name},

---

### 🌟 HESAPLAMA ÖZETİ

**Temel Enerji:** [Bir cümlede ana karakter]

**Mevcut Dönem:** [Şu an hangi kozmik dönemdesin]

**Öne Çıkan Tema:** [En güçlü etki]

**Dikkat Noktası:** [Farkında olunması gereken]

---
Detaylı analizler için Orbis sekmesindeki kategorileri incele.
"""


# ==========================================
# YARDIMCI FONKSİYONLAR
# ==========================================

def safe_get(data, key, default=None):
    """Dict'ten güvenli veri çekme."""
    if isinstance(data, dict):
        return data.get(key, default)
    return default

# Alias
get_data = safe_get


def filter_by_weight(data, min_weight=4):
    """Ağırlığa göre aspect filtreleme."""
    if not isinstance(data, dict):
        return {}

    filtered = {}
    for k, v in data.items():
        if not isinstance(v, dict):
            continue
        aspects = v.get("aspects", [])
        strong_aspects = [a for a in aspects if a.get("weight", 0) >= min_weight]
        if strong_aspects:
            filtered[k] = {**v, "aspects": strong_aspects}

    return filtered


def build_critical_life_periods(astro_data):
    """Kritik yaşam dönemlerini çıkar."""
    return {
        "critical_life_periods": safe_get(astro_data, "critical_life_periods", [])
    }


def build_psychological_core(astro_data):
    """Psikolojik çekirdek verilerini çıkar."""
    return {
        "psychological_core": {
            "core_midpoints": filter_by_weight(
                safe_get(astro_data, "natal_midpoint_analysis"), min_weight=5
            ),
            "moon_pluto_dynamics": safe_get(astro_data, "moon_pluto_aspects", []),
            "saturn_core_themes": safe_get(astro_data, "saturn_aspects", [])
        }
    }


def build_karmic_themes(astro_data):
    """Karmik tema verilerini çıkar."""
    return {
        "karmic_themes": {
            "node_midpoints": filter_by_weight(
                safe_get(astro_data, "node_midpoints"), min_weight=4
            ),
            "dasa_cycles": safe_get(astro_data, "vimshottari_dasa", {}),
            "karmic_fixed_stars": safe_get(astro_data, "natal_fixed_stars", [])
        }
    }

# Türkçe ay isimleri
TURKISH_MONTHS = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}


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

def get_today_formatted():
    """Bugünün tarihini Türkçe formatla."""
    now = datetime.now()
    return f"{now.day} {TURKISH_MONTHS[now.month]} {now.year}"


def format_date_turkish(date_obj):
    """Herhangi bir tarihi Türkçe formatla."""
    if isinstance(date_obj, str):
        return date_obj  # Zaten string ise olduğu gibi döndür
    if hasattr(date_obj, 'day'):
        return f"{date_obj.day} {TURKISH_MONTHS[date_obj.month]} {date_obj.year}"
    return str(date_obj)


# ==========================================
# PROMPT HAZIRLAMA
# ==========================================

def prepare_interpretation_prompt(interpretation_type, astro_data, user_name, **kwargs):
    """
    Yorum tipi ve veriye göre prompt hazırla.

    Args:
        interpretation_type: Yorum tipi (natal, daily, transit, vb.)
        astro_data: Astrolojik hesaplama verileri
        user_name: Kullanıcı adı
        **kwargs: Ek parametreler (date, duration, period, vb.)

    Returns:
        str: Hazırlanmış prompt
    """

    # Tarih parametrelerini al (varsayılanlarla)
    date = kwargs.get('date', kwargs.get('tarih', get_today_formatted()))
    start_date = kwargs.get('start_date', kwargs.get('baslangic_tarihi', get_today_formatted()))
    end_date = kwargs.get('end_date', kwargs.get('bitis_tarihi', ''))
    period = kwargs.get('period', kwargs.get('donem', '2025'))
    duration = kwargs.get('duration', kwargs.get('sure', '2 hafta'))

    # Tür normalleştirme
    type_map = {
        "birth_chart": "natal",
        "relationship": "relationship",
        "transits": "transit",
        "daily": "daily",
        "short_term": "short_term",
        "long_term": "long_term",
        "career": "career",
        "financial": "financial",
        "psychological_karmic": "psychological_karmic",
        # Yeni kategoriler
        "vedic": "vedic",
        "eclipse": "eclipse",
        "harmonic": "harmonic",
        "esoteric": "esoteric",
        "timing": "timing",
        "health": "health",
        "summary": "summary"
    }
    norm_type = type_map.get(interpretation_type, interpretation_type)

    # Format parametreleri
    format_params = {
        "user_name": user_name,
        "date": date,
        "start_date": start_date,
        "end_date": end_date,
        "period": period,
        "duration": duration,
        # Backward compatibility for templates
        "tarih": date,
        "baslangic_tarihi": start_date,
        "bitis_tarihi": end_date,
        "donem": period,
        "sure": duration
    }

    # -------------------------
    # DAILY ANALİZ
    # -------------------------
    if norm_type == "daily":
        payload = {
            "transit_positions": get_data(astro_data, "transit_positions"),
            "transit_houses": get_data(astro_data, "transit_houses"),
            "transit_aspects": get_data(astro_data, "transit_aspects"),
            "transit_to_natal": get_data(astro_data, "transit_to_natal_aspects"),
            "lunar_return": get_data(astro_data, "lunar_return_chart"),
            "azimuth_altitude": get_data(astro_data, "transit_azimuth_altitude"),
        }
        prompt = DAILY_ANALYSIS_PROMPT.format(**format_params)
        data_str = json.dumps(payload,  ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # NATAL ANALİZ
    # -------------------------
    elif norm_type == "natal":
        payload = {
            "planet_positions": get_data(astro_data, "natal_planet_positions"),
            "houses": get_data(astro_data, "natal_houses"),
            "aspects": get_data(astro_data, "natal_aspects"),
            "dignities": get_data(astro_data, "natal_dignity_scores"),
            "midpoints": get_data(astro_data, "natal_midpoint_analysis"),
            "part_of_fortune": get_data(astro_data, "natal_part_of_fortune"),
            "arabic_parts": get_data(astro_data, "natal_arabic_parts"),
            "fixed_stars": get_data(astro_data, "natal_fixed_stars"),
            "declinations": get_data(astro_data, "natal_declinations"),
        }
        prompt = NATAL_ANALYSIS_PROMPT.format(**format_params)
        data_str = json.dumps(payload,  ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # TRANSİT ANALİZ
    # -------------------------
    elif norm_type == "transit":
        payload = {
            "transit_positions": get_data(astro_data, "transit_positions"),
            "transit_houses": get_data(astro_data, "transit_houses"),
            "transit_aspects": get_data(astro_data, "transit_aspects"),
            "transit_to_natal": get_data(astro_data, "transit_to_natal_aspects"),
            "azimuth_altitude": get_data(astro_data, "transit_azimuth_altitude"),
        }
        prompt = TRANSIT_ANALYSIS_PROMPT.format(**format_params)
        data_str = json.dumps(payload,  ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # KISA VADELİ ÖNGÖRÜ
    # -------------------------
    elif norm_type == "short_term":
        payload = {
            "lunar_return": get_data(astro_data, "lunar_return_chart"),
            "progressed_moon_phase": get_data(astro_data, "progressed_moon_phase"),
            "progressed_aspects": get_data(astro_data, "progressed_aspects"),
            "transit_to_natal": get_data(astro_data, "transit_to_natal_aspects"),
            "transit_houses": get_data(astro_data, "transit_houses"),
        }
        prompt = SHORT_TERM_FORECAST_PROMPT.format(**format_params)
        data_str = json.dumps(payload,  ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # UZUN VADELİ ÖNGÖRÜ
    # -------------------------
    elif norm_type == "long_term":
        payload = {
            "solar_return": get_data(astro_data, "solar_return_chart"),
            "solar_arc": get_data(astro_data, "solar_arc_progressions"),
            "secondary_progressions": get_data(astro_data, "secondary_progressions"),
            "progressed_aspects": get_data(astro_data, "progressed_aspects"),
            "firdaria": get_data(astro_data, "firdaria_periods"),
            "vimshottari": get_data(astro_data, "vimshottari_dasa"),
        }
        prompt = LONG_TERM_FORECAST_PROMPT.format(**format_params)
        data_str = json.dumps(payload,  ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # KARİYER ANALİZİ
    # -------------------------
    elif norm_type == "career":
        payload = {
            "natal_houses": get_data(astro_data, "natal_houses"),
            "natal_planets": get_data(astro_data, "natal_planet_positions"),
            "midpoints": filter_by_weight(get_data(astro_data, "natal_midpoint_analysis"), 4),
            "solar_arc": get_data(astro_data, "solar_arc_progressions"),
            "transit_to_natal": get_data(astro_data, "transit_to_natal_aspects"),
            "firdaria": get_data(astro_data, "firdaria_periods"),
        }
        prompt = CAREER_ANALYSIS_PROMPT.format(**format_params)
        data_str = json.dumps(payload,  ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # FİNANSAL ANALİZ
    # -------------------------
    elif norm_type == "financial":
        payload = {
            "natal_houses": get_data(astro_data, "natal_houses"),
            "part_of_fortune": get_data(astro_data, "natal_part_of_fortune"),
            "arabic_parts": get_data(astro_data, "natal_arabic_parts"),
            "transit_to_natal": get_data(astro_data, "transit_to_natal_aspects"),
            "vimshottari": get_data(astro_data, "vimshottari_dasa"),
            "solar_return": get_data(astro_data, "solar_return_chart"),
        }
        prompt = FINANCIAL_ANALYSIS_PROMPT.format(**format_params)
        data_str = json.dumps(payload,  ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # İLİŞKİ ANALİZİ
    # -------------------------
    elif norm_type == "relationship":
        payload = {
            "natal_planets": get_data(astro_data, "natal_planet_positions"),
            "natal_houses": get_data(astro_data, "natal_houses"),
            "midpoints": filter_by_weight(get_data(astro_data, "natal_midpoint_analysis"), 4),
            "transit_to_natal": get_data(astro_data, "transit_to_natal_aspects"),
            "lunar_return": get_data(astro_data, "lunar_return_chart"),
        }
        prompt = RELATIONSHIP_ANALYSIS_PROMPT.format(**format_params)
        data_str = json.dumps(payload,  ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # PSİKOLOJİK/KARMİK ANALİZ
    # -------------------------
    elif norm_type == "psychological_karmic":
        payload = {
            "critical_periods": build_critical_life_periods(astro_data),
            "psychological_core": build_psychological_core(astro_data),
            "karmic_themes": build_karmic_themes(astro_data),
        }
        prompt = PSYCHOLOGICAL_KARMIC_PROMPT.format(**format_params)
        data_str = json.dumps(payload,  ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # VEDİK ANALİZ (YENİ)
    # -------------------------
    elif norm_type == "vedic":
        payload = {
            "vimshottari_dasa": get_data(astro_data, "vimshottari_dasa"),
            "navamsa_chart": get_data(astro_data, "navamsa_chart"),
            "natal_additional_points": get_data(astro_data, "natal_additional_points"),
            "natal_planets": get_data(astro_data, "natal_planet_positions"),
            "natal_houses": get_data(astro_data, "natal_houses"),
        }
        prompt = VEDIC_ANALYSIS_PROMPT.format(**format_params)
        data_str = json.dumps(payload, ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # TUTULMA ANALİZİ (YENİ)
    # -------------------------
    elif norm_type == "eclipse":
        payload = {
            "eclipses_nearby_birth": get_data(astro_data, "eclipses_nearby_birth"),
            "eclipses_nearby_current": get_data(astro_data, "eclipses_nearby_current"),
            "natal_lunation_cycle": get_data(astro_data, "natal_lunation_cycle"),
            "natal_additional_points": get_data(astro_data, "natal_additional_points"),
            "transit_to_natal": get_data(astro_data, "transit_to_natal_aspects"),
        }
        prompt = ECLIPSE_ANALYSIS_PROMPT.format(**format_params)
        data_str = json.dumps(payload, ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # HARMONİK ANALİZ (YENİ)
    # -------------------------
    elif norm_type == "harmonic":
        payload = {
            "deep_harmonic_analysis": get_data(astro_data, "deep_harmonic_analysis"),
            "navamsa_chart": get_data(astro_data, "navamsa_chart"),
            "natal_planets": get_data(astro_data, "natal_planet_positions"),
            "natal_aspects": get_data(astro_data, "natal_aspects"),
        }
        prompt = HARMONIC_ANALYSIS_PROMPT.format(**format_params)
        data_str = json.dumps(payload, ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # EZOTERİK ANALİZ (YENİ)
    # -------------------------
    elif norm_type == "esoteric":
        payload = {
            "natal_antiscia": get_data(astro_data, "natal_antiscia"),
            "natal_additional_points": get_data(astro_data, "natal_additional_points"),
            "natal_fixed_stars": get_data(astro_data, "natal_fixed_stars"),
            "natal_planets": get_data(astro_data, "natal_planet_positions"),
            "natal_houses": get_data(astro_data, "natal_houses"),
        }
        prompt = ESOTERIC_ANALYSIS_PROMPT.format(**format_params)
        data_str = json.dumps(payload, ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # ZAMANLAMA ANALİZİ (YENİ)
    # -------------------------
    elif norm_type == "timing":
        payload = {
            "firdaria": get_data(astro_data, "firdaria_periods"),
            "vimshottari": get_data(astro_data, "vimshottari_dasa"),
            "progressed_positions": get_data(astro_data, "progressed_positions"),
            "progressed_moon_phase": get_data(astro_data, "progressed_moon_phase"),
            "solar_arc": get_data(astro_data, "solar_arc_progressions"),
            "secondary_progressions": get_data(astro_data, "secondary_progressions"),
            "transit_to_natal": get_data(astro_data, "transit_to_natal_aspects"),
        }
        prompt = TIMING_ANALYSIS_PROMPT.format(**format_params)
        data_str = json.dumps(payload, ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # SAĞLIK/ENERJİ ANALİZİ (YENİ)
    # -------------------------
    elif norm_type == "health":
        payload = {
            "natal_declinations": get_data(astro_data, "natal_declinations"),
            "natal_azimuth_altitude": get_data(astro_data, "natal_azimuth_altitude"),
            "natal_dignity_scores": get_data(astro_data, "natal_dignity_scores"),
            "natal_planets": get_data(astro_data, "natal_planet_positions"),
            "natal_houses": get_data(astro_data, "natal_houses"),
            "transit_to_natal": get_data(astro_data, "transit_to_natal_aspects"),
        }
        prompt = HEALTH_ENERGY_PROMPT.format(**format_params)
        data_str = json.dumps(payload, ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # ÖZET ANALİZ (YENİ)
    # -------------------------
    elif norm_type == "summary":
        payload = {
            "natal_ascendant": get_data(astro_data, "natal_ascendant"),
            "natal_planets": get_data(astro_data, "natal_planet_positions"),
            "vimshottari": get_data(astro_data, "vimshottari_dasa"),
            "firdaria": get_data(astro_data, "firdaria_periods"),
            "transit_to_natal": get_data(astro_data, "transit_to_natal_aspects"),
        }
        prompt = SUMMARY_PROMPT.format(**format_params)
        data_str = json.dumps(payload, ensure_ascii=False, default=str)
        return f"{prompt}\n\nVERİLER:\n{data_str}"

    # -------------------------
    # FALLBACK - GENEL ANALİZ
    # -------------------------
    else:
        data_str = json.dumps(astro_data,  ensure_ascii=False, default=str)
        prompt = GENERIC_ANALYSIS_PROMPT.format(**format_params)
        return f"{prompt}\n\nVERİLER:\n{data_str}"


# ==========================================
# LLM ÇAĞRI FONKSİYONLARI
# ==========================================

def call_deepseek(prompt: str) -> str:
    """DeepSeek API çağrısı."""
    if not DEEPSEEK_API_KEY:
        raise ValueError("DeepSeek API key bulunamadı")

    import httpx
    # DeepSeek için daha uzun timeout ve güvenli client
    http_client = httpx.Client(
        timeout=httpx.Timeout(90.0, connect=10.0),
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
    )

    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
        http_client=http_client
    )

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # deepseek-reasoner yerine daha hızlı olan chat modelini denebilir veya kullanıcı tercihi
            messages=[
                {"role": "system", "content": "Sen Orbis astroloji platformunun uzman yorum motorusun. Profesyonel, derinlikli ve samimi Türkçe yanıtlar ver."},
                {"role": "user", "content": prompt}
            ],
    
            temperature=0.3,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"DeepSeek API Hatası: {str(e)}")
        raise
    finally:
        http_client.close()


def call_openrouter(prompt: str) -> str:
    """OpenRouter API çağrısı (fallback)."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OpenRouter API key bulunamadı")

    import httpx
    http_client = httpx.Client(timeout=httpx.Timeout(60.0))

    client = OpenAI(
        api_key=OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        http_client=http_client
    )

    try:
        # Daha güvenilir bir model seçimi
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-001", # Ücretsiz modeller bazen kararsız olabilir
            messages=[
                {"role": "system", "content": "Sen deneyimli bir astrologsun. Türkçe yanıt ver."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=4000
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenRouter API Hatası: {str(e)}")
        raise
    finally:
        http_client.close()


def call_llm_with_fallback(prompt: str) -> str:
    """
    LLM çağrısı - fallback zinciri ve retry mekanizması ile.
    Sıra: DeepSeek -> Gemini -> OpenRouter
    Her bir sağlayıcı için 2 deneme yapılır.
    """
    errors = []

    # Sağlayıcıları ve fonksiyonlarını tanımla
    providers = []
    if DEEPSEEK_API_KEY:
        providers.append(("DeepSeek", call_deepseek))
    if OPENROUTER_API_KEY:
        providers.append(("OpenRouter", call_openrouter))

    for name, func in providers:
        for attempt in range(2):  # Her sağlayıcı için 2 deneme
            try:
                if attempt > 0:
                    print(f"{Colors.YELLOW}🔄 {name} yeniden deneniyor (Deneme {attempt + 1})...{Colors.END}")
                    time.sleep(2 ** attempt)  # Üstel bekleme

                print(f"{Colors.CYAN}{Colors.BOLD}🔄 LLM API Deneniyor:{Colors.END} {Colors.YELLOW}{name}{Colors.END}")
                result = func(prompt)

                if not result or len(result.strip()) < 10:
                    raise ValueError(f"{name} boş veya çok kısa yanıt döndürdü.")

                print(f"{Colors.GREEN}{Colors.BOLD}✅ {name} başarılı!{Colors.END}")
                return result

            except Exception as e:
                error_detail = f"{name} (Deneme {attempt + 1}): {str(e)}"
                errors.append(error_detail)
                print(f"{Colors.RED}❌ {error_detail}{Colors.END}")

                # Eğer son denemeyse ve başka sağlayıcı yoksa veya tümü başarısız olacaksa devam et
                continue

    # Tüm API'ler başarısız
    error_msg = " | ".join(errors) if errors else "Hiçbir LLM API yapılandırılmamış"
    print(f"{Colors.BG_YELLOW}{Colors.RED}{Colors.BOLD}⚠️ TÜM LLM API'LERİ BAŞARISIZ!{Colors.END}")
    raise RuntimeError(f"Tüm LLM API'leri başarısız: {error_msg}")


# ==========================================
# ANA API FONKSİYONLARI
# ==========================================

def get_ai_interpretation_engine(astro_data: dict, interpretation_type: str, user_name: str, **kwargs) -> dict:
    """
    Ana AI yorum motoru.
    
    Args:
        astro_data: Astrolojik hesaplama verileri
        interpretation_type: Yorum tipi (natal, daily, transit, vb.)
        user_name: Kullanıcı adı
        **kwargs: Ek parametreler (tarih, sure, donem, vb.)
    
    Returns:
        dict: {"success": bool, "interpretation": str, "error": str|None}
    """
    try:
        # Prompt hazırla
        prompt = prepare_interpretation_prompt(
            interpretation_type=interpretation_type,
            astro_data=astro_data,
            user_name=user_name,
            **kwargs
        )
        
        # 🎨 Renkli Debug Çıktısı - İstek
        data_preview = {
            "interpretation_type": interpretation_type,
            "user_name": user_name,
            "astro_data_keys": list(astro_data.keys()) if isinstance(astro_data, dict) else "N/A",
            "astro_data_key_count": len(astro_data.keys()) if isinstance(astro_data, dict) else 0,
            "extra_params": kwargs if kwargs else "Yok"
        }
        print_ai_request_debug(interpretation_type, user_name, prompt, data_preview)
        
        # LLM çağrısı yap
        interpretation = call_llm_with_fallback(prompt)
        
        # Emoji'leri temizle (Android TalkBack erişilebilirlik için)
        interpretation = remove_emojis(interpretation)
        
        # 🎨 Renkli Debug Çıktısı - Başarılı Yanıt
        print_ai_response_debug(True, interpretation_type, interpretation)
        
        return {
            "success": True,
            "interpretation": interpretation,
            "interpretation_type": interpretation_type,
            "error": None
        }
        
    except Exception as e:
        # 🎨 Renkli Debug Çıktısı - Hata
        print_ai_response_debug(False, interpretation_type, error=str(e))
        logging.error(f"AI yorum hatası ({interpretation_type}): {str(e)}")
        return {
            "success": False,
            "interpretation": None,
            "interpretation_type": interpretation_type,
            "error": str(e)
        }
