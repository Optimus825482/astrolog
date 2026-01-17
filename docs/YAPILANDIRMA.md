# ⚙️ Yapılandırma Rehberi

Astro AI Predictor, "Twelve-Factor App" metodolojisine uygun olarak, tüm yapılandırmasını ortam değişkenleri (environment variables) üzerinden yönetir.

Bu ayarlar `env_config.py` modülü tarafından doğrulanır ve `config.py` üzerinden uygulamaya sunulur.

## `.env` Dosyası

Uygulamanın kök dizininde bir `.env` dosyası oluşturmalısınız.

### Temel Ayarlar

| Değişken | Açıklama | Varsayılan | Zorunlu? |
|----------|----------|------------|----------|
| `FLASK_ENV` | Çalışma modu (`development` veya `production`). | `development` | Hayır |
| `FLASK_DEBUG` | Hata ayıklama modu. Prod'da `False` olmalı. | `False` | Hayır |
| `SECRET_KEY` | Session güvenliği için rastgele string. | - | **Evet (Prod)** |

### Veritabanı ve Önbellek (Redis)

Redis, API yanıtlarını ve oturum verilerini önbelleğe almak için kullanılır.

| Değişken | Açıklama | Varsayılan |
|----------|----------|------------|
| `REDIS_HOST` | Redis sunucu adresi. | `localhost` |
| `REDIS_PORT` | Redis portu. | `6379` |
| `REDIS_PASSWORD` | Redis şifresi (varsa). | - |
| `CACHE_TYPE` | Cache tipi (`redis` veya `simple`). | `simple` |

### Harici Servis API Anahtarları

Uygulamanın tam fonksiyonel çalışması için aşağıdaki servislerin anahtarları gereklidir.

| Değişken | Servis | Kullanım Amacı | Zorunluluk |
|----------|--------|----------------|------------|
| `OPENCAGE_API_KEY` | [OpenCage](https://opencagedata.com/) | Şehir/Konum arama ve koordinat bulma. | **Kritik** |
| `DEEPSEEK_API_KEY` | [DeepSeek](https://deepseek.com/) | Birincil AI yorum motoru (en yüksek kalite). | Önerilen |
| `OPENROUTER_API_KEY`| [OpenRouter](https://openrouter.ai/) | Yedek AI motoru (Claude, GPT-4, Llama erişimi). | Önerilen |
| `ZAI_API_KEY` | Zai (GLM-4) | Alternatif AI motoru. | Opsiyonel |

### Güvenlik Ayarları (Production)

Production ortamında (Vercel, Railway, Heroku vb.) bu ayarların yapıldığından emin olun.

| Değişken | Açıklama | Önerilen |
|----------|----------|----------|
| `SESSION_COOKIE_SECURE` | Sadece HTTPS üzerinden cookie gönderimi. | `True` |
| `CORS_ORIGINS` | İzin verilen frontend domainleri (virgülle ayrılmış). | `https://siteniz.com` |

## Örnek `.env` Dosyası

```ini
FLASK_ENV=development
FLASK_DEBUG=True
SECRET_KEY=cok-gizli-ve-uzun-bir-anahtar-123456

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
CACHE_TYPE=redis

# APIs
OPENCAGE_API_KEY=oc_123...
DEEPSEEK_API_KEY=sk-123...
```
