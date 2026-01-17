# 🏗️ Sistem Mimarisi

Astro AI Predictor, modülerlik, test edilebilirlik ve sürdürülebilirlik ilkeleri gözetilerek **Servis Tabanlı Mimari (Service-Oriented Architecture)** ile tasarlanmıştır.

## Dizin Yapısı ve Sorumluluklar

```
backend/flask_app/
├── api/                # Serverless (Vercel) giriş noktası
├── routes/             # HTTP Kontrolcüleri (Controllers)
│   ├── main.py         # Ana uygulama endpointleri
│   └── admin.py        # Yönetim paneli
├── services/           # İş Mantığı (Business Logic)
│   ├── astro_service.py # Astrolojik hesaplama motoru
│   ├── ai_service.py    # AI entegrasyon katmanı
│   └── location_service.py # Konum servisleri
├── static/             # Frontend varlıkları (CSS, JS)
├── templates/          # Jinja2 HTML şablonları
└── tests/              # Birim ve entegrasyon testleri
```

## Temel Bileşenler

### 1. AstroService (`services/astro_service.py`)
Uygulamanın çekirdeğidir. `pyswisseph` (NASA JPL verileri) kütüphanesini sarmalar ve ham astronomik veriyi anlamlı astrolojik verilere dönüştürür.

*   **Sorumlulukları:**
    *   Julian Day dönüşümleri.
    *   Gezegen pozisyonlarının (Boylam, Enlem, Hız) hesaplanması.
    *   Ev sistemleri (Placidus, Koch, vb.) hesaplaması.
    *   Açılar (Aspects), Transitler, Progresyonlar ve Solar Arc hesaplamaları.
*   **Özellik:** `Stateless` (Durumsuz) çalışır. Her hesaplama izole ve deterministiktir.

### 2. AIService (`services/ai_service.py`)
Astrolojik verileri doğal dile döken "Yorumlayıcı" katmandır.

*   **Sorumlulukları:**
    *   Hesaplanan veriyi optimize edilmiş promptlara dönüştürmek.
    *   LLM Sağlayıcıları (DeepSeek, OpenRouter) ile iletişim kurmak.
    *   **Fallback Mekanizması:** Birincil API yanıt vermezse, otomatik olarak yedek sağlayıcıya geçer.
    *   **Async/Sync Desteği:** Uzun süren yorumlama işlemlerini bloklamadan yapar.

### 3. LocationService (`services/location_service.py`)
Coğrafi verileri yönetir.

*   **Sorumlulukları:**
    *   Şehir isminden koordinat bulma (Geocoding).
    *   Zaman dilimi (Timezone) tespiti.
    *   Sonuçların önbelleğe alınması (Redis).

## Tasarım Desenleri (Design Patterns)

*   **Factory Pattern:** Flask uygulaması `create_app()` fonksiyonu ile oluşturulur. Bu, test ve production ortamları için farklı konfigürasyonların kolayca yüklenmesini sağlar.
*   **Dependency Injection:** Servisler, route handler'lara doğrudan import edilerek değil, modüler yapılar üzerinden sunulur.
*   **Decorator Pattern:** Caching (`@cached_astro_calculation`) ve hata yönetimi için Python decorator'ları yoğun olarak kullanılır.

## Veri Akışı

1.  **İstek:** Kullanıcı formu doldurur (`POST /results`).
2.  **Validasyon:** `routes/main.py` giriş verilerini doğrular.
3.  **Hesaplama:** `AstroService` ham veriyi işler.
4.  **Zenginleştirme:** (İsteğe bağlı) `AIService` veriyi yorumlar.
5.  **Önbellekleme:** Sonuçlar `cache_config.py` kurallarına göre Redis'e yazılır.
6.  **Yanıt:** `new_result.html` şablonu render edilerek kullanıcıya sunulur.
