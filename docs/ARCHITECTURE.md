# Proje Mimarisi ve Geliştirme Rehberi

Astro AI Predictor, modüler bir Flask uygulaması olarak tasarlanmıştır.

## Dizin Yapısı

```
backend/flask_app/
├── services/           # İş mantığı katmanı (Business Logic)
│   ├── astro_service.py # Astrolojik hesaplamalar (Swisseph wrapper)
│   ├── ai_service.py    # AI entegrasyonu (OpenAI/DeepSeek)
│   └── location_service.py # Geocoding işlemleri
├── routes/             # HTTP endpoint tanımları (Blueprints)
│   ├── main.py         # Ana uygulama rotaları
│   └── admin.py        # Yönetim paneli
├── static/             # CSS, JS, görsel varlıklar
├── templates/          # Jinja2 HTML şablonları
├── tests/              # Pytest testleri
├── cache_config.py     # Redis cache yapılandırması
├── config.py           # Flask yapılandırma sınıfı
├── env_config.py       # Çevresel değişken yönetimi
└── extensions.py       # Flask eklentileri (CORS, Cache vb.)
```

## Servis Katmanı

### AstroService (`services/astro_service.py`)
Uygulamanın kalbidir. `pyswisseph` kütüphanesini kullanarak tüm gök cismi pozisyonlarını hesaplar.
- **Stateless**: Her hesaplama bağımsızdır, state tutmaz.
- **Hassasiyet**: NASA JPL efemeris dosyalarını (`sepl_00.se1`, vb.) kullanır.
- **Önemli Metod:** `calculate_astro_data(...)` -> Tüm haritayı (evler, açılar, gezegenler) tek seferde hesaplar.

### AIService (`services/ai_service.py`)
Astrolojik verileri doğal dile çevirir.
- **Fallback Mekanizması**: Önce DeepSeek API'yi dener, başarısız olursa OpenRouter (Gemini/Claude) üzerinden dener.
- **Async Desteği**: Uzun süren AI işlemlerini bloklamamak için `async/await` yapısını destekler (Flask route'ları içinde sync wrapper kullanılır).

## Geliştirme Kuralları

1.  **Monolitik Yapıdan Kaçının**: Yeni bir özellik eklerken, mantığı `routes` dosyasında değil, ilgili `services` dosyasında yazın.
2.  **Tip Güvenliği**: Mümkün olduğunca Python Type Hints kullanın.
3.  **Hata Yönetimi**: `exceptions.py` içindeki özel hata sınıflarını (`AstroError`, `InvalidDateError`) kullanın.
4.  **Config**: Hardcoded değerler kullanmayın. `env_config.py` üzerinden `.env` değişkenlerini okuyun.

## Performans İpuçları

*   **Caching**: `cache_config.py` içindeki decorator'ları kullanın.
    *   `@cached_astro_calculation`: Astrolojik hesaplamalar deterministiktir, yoğun cache'lenmelidir.
    *   `@cached_ai_interpretation`: AI yanıtları pahalıdır, mutlaka cache'lenmelidir.
*   **Lazy Loading**: Ağır kütüphaneleri (örn. `pandas` veya büyük veri setleri) sadece ihtiyaç duyulan fonksiyon içinde import edin (gerekirse).

## Dağıtım (Deployment)

Uygulama WSGI uyumludur (`wsgi.py`). Gunicorn veya uWSGI ile çalıştırılabilir.
Vercel/Netlify gibi serverless ortamlar için `api/index.py` giriş noktası mevcuttur.

### Redis
Production ortamında `REDIS_HOST` tanımlanmalıdır. Development'ta `SimpleCache` (memory) fallback olarak çalışır.
