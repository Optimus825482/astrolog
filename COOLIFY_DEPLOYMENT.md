# 🚀 ORBIS Backend - Coolify Deployment Kılavuzu

## 📋 Gereksinimler

- Coolify kurulu bir sunucu
- Git repository (GitHub, GitLab veya Coolify'ın desteklediği bir provider)
- Domain adı (opsiyonel ama önerilir)

---

## 🔧 Adım 1: Dosyaları Git'e Push Et

```bash
cd d:\astro-ai-predictor\backend\flask_app

# Yeni branch oluştur (opsiyonel)
git checkout -b production

# Değişiklikleri commit et
git add Dockerfile docker-compose.yml .dockerignore
git commit -m "feat: Coolify deployment files"

# Push et
git push origin production
```

---

## 🌐 Adım 2: Coolify'da Yeni Proje Oluştur

1. **Coolify Dashboard'a gir**
2. **"New Resource" → "Application" seç**
3. **Source olarak Git repository'ni seç**
   - GitHub/GitLab bağlantını yap
   - Repository: `astro-ai-predictor`
   - Branch: `production` (veya main)
   - Build Path: `/backend/flask_app`

---

## 🐳 Adım 3: Build Ayarları

Coolify'da şu ayarları yap:

| Ayar | Değer |
|------|-------|
| **Build Pack** | `Dockerfile` |
| **Dockerfile Location** | `Dockerfile` |
| **Port** | `8000` |
| **Health Check Path** | `/api/health` |

---

## 🔐 Adım 4: Environment Variables

Coolify'da **Settings → Environment Variables** bölümünde şunları ekle:

```env
# Flask Settings
FLASK_ENV=production
DEBUG=False
PORT=8000
SECRET_KEY=<güçlü-random-key-oluştur>

# OpenAI API Key (AI yorumlar için)
OPENAI_API_KEY=sk-...

# Google API Key (opsiyonel)
GOOGLE_API_KEY=...

# Redis Cache (opsiyonel - Coolify'da Redis eklediysen)
REDIS_URL=redis://redis:6379/0
```

### Firebase Credentials Ekleme

**Yöntem 1: Base64 Encoded (Önerilen)**

```bash
# Local'de credentials dosyasını base64'e çevir
base64 -i orbis-ffa9e-firebase-adminsdk-fbsvc-b4ac1afabf.json

# Çıktıyı Coolify'da environment variable olarak ekle:
FIREBASE_CREDENTIALS_BASE64=<base64-output>
```

Sonra `__init__.py`'a şu kodu ekle:
```python
import base64
import json
import os

firebase_b64 = os.getenv("FIREBASE_CREDENTIALS_BASE64")
if firebase_b64:
    creds = json.loads(base64.b64decode(firebase_b64))
    # Firebase'i bu creds ile başlat
```

**Yöntem 2: Volume Mount**
- Coolify'da Storage ekle
- Firebase JSON dosyasını upload et
- Path: `/app/firebase-credentials.json`

---

## 🌍 Adım 5: Domain Ayarları

1. **Coolify → Application → Settings → Domains**
2. Domain ekle: `api.orbisapp.com` (veya istediğin subdomain)
3. **SSL/TLS**: Let's Encrypt otomatik aktif olacak
4. **Proxy**: Traefik (Coolify default)

---

## 📡 Adım 6: Deploy Et

1. **"Deploy" butonuna tıkla**
2. Build loglarını takip et
3. Health check geçene kadar bekle

---

## ✅ Adım 7: Test Et

```bash
# Health check
curl https://api.orbisapp.com/api/health

# Beklenen çıktı:
# {"status": "healthy", "service": "orbis-backend", "version": "1.0.0"}
```

---

## 📱 Adım 8: Mobile App'i Güncelle

Mobile app'teki API URL'lerini güncelle:

### `mobile/www/js/config.js` veya benzeri dosya:
```javascript
const API_BASE_URL = 'https://api.orbisapp.com';
```

### Android `capacitor.config.ts`:
```typescript
const config: CapacitorConfig = {
  server: {
    url: 'https://api.orbisapp.com',
    cleartext: false
  }
};
```

---

## 🔄 Auto-Deploy Ayarları

Coolify'da otomatik deploy için:

1. **Settings → Webhooks** bölümüne git
2. GitHub/GitLab webhook URL'ini al
3. Repository settings'de webhook ekle
4. Artık her push'ta otomatik deploy olacak!

---

## 📊 Monitoring

Coolify şunları otomatik sağlar:
- **Logs**: Real-time container logs
- **Metrics**: CPU, Memory, Network
- **Alerts**: Slack/Discord/Email bildirimleri

---

## 🔧 Troubleshooting

### Build Hatası
```bash
# Logs'u kontrol et
# Coolify Dashboard → Application → Logs
```

### Container Başlamıyor
```bash
# Health check'i manuel test et
docker exec -it orbis-backend curl http://localhost:8000/api/health
```

### Memory/CPU Sorunları
- Coolify → Application → Resources
- Memory Limit: 512MB-1GB önerilir
- CPU Limit: 0.5-1 core

---

## 🗂️ Dosya Yapısı

```
flask_app/
├── Dockerfile              ✅ Oluşturuldu
├── docker-compose.yml      ✅ Oluşturuldu  
├── .dockerignore           ✅ Oluşturuldu
├── requirements.txt        ✅ Mevcut
├── wsgi.py                 ✅ Mevcut
├── __init__.py             ✅ Health endpoint eklendi
└── ephe/                   ✅ Ephemeris dosyaları
```

---

## 🚀 Hızlı Başlangıç Komutları

```bash
# 1. Git push
git add . && git commit -m "Deploy to Coolify" && git push

# 2. Coolify'da "Deploy" tıkla

# 3. Test et
curl https://your-domain.com/api/health
```

---

## 💡 İpuçları

1. **Redis Ekle**: Coolify'da "New Resource" → "Database" → "Redis" ile hızlı cache
2. **Backup**: Coolify otomatik backup yapabilir
3. **Scaling**: Replicas sayısını artırarak horizontal scale
4. **Rollback**: Coolify'da önceki deploy'a kolayca dön

---

## 📞 Destek

Sorun yaşarsan:
1. Coolify Docs: https://coolify.io/docs
2. GitHub Issues: Proje repository'sinde issue aç
