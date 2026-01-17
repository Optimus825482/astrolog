# 🚀 Kurulum ve Geliştirme Rehberi

Bu rehber, Astro AI Predictor backend projesini yerel geliştirme ortamınızda nasıl kuracağınızı adım adım anlatır.

## Ön Gereksinimler

Kuruluma başlamadan önce aşağıdaki araçların sisteminizde yüklü olduğundan emin olun:

*   **Python 3.10+**: [İndir](https://www.python.org/downloads/)
*   **Node.js 18+ & npm**: [İndir](https://nodejs.org/) (Statik varlıklar ve Tailwind CSS için)
*   **Redis**: [Windows için](https://github.com/microsoftarchive/redis/releases) veya [Docker ile](https://hub.docker.com/_/redis) (Caching mekanizması için zorunludur)
*   **Git**: [İndir](https://git-scm.com/)

## 1. Projeyi Klonlama

```bash
git clone https://github.com/kullaniciadi/astro-ai-predictor.git
cd astro-ai-predictor/backend/flask_app
```

## 2. Python Sanal Ortam (Virtual Environment)

Bağımlılıkları izole etmek için bir sanal ortam oluşturun:

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

## 3. Python Bağımlılıkları

Gerekli kütüphaneleri `requirements.txt` dosyasından yükleyin:

```bash
pip install -r requirements.txt
```

> **Not:** `pyswisseph` kütüphanesi derleme gerektirebilir. Windows'ta hata alırsanız, C++ Build Tools yüklü olduğundan emin olun.

## 4. Frontend Varlıkları (Tailwind CSS)

Proje, stil işlemleri için Tailwind CSS kullanır. Node.js bağımlılıklarını yükleyin:

```bash
npm install
```

CSS dosyasını derlemek için (geliştirme modunda izleme):

```bash
npm run watch
```

## 5. Ortam Değişkenleri (.env)

Projenin kök dizinindeki `.env.example` dosyasını `.env` olarak kopyalayın:

```bash
cp .env.example .env
```

`.env` dosyasını açın ve gerekli API anahtarlarını girin (Detaylar için: [Yapılandırma](YAPILANDIRMA.md)).

## 6. Uygulamayı Başlatma

### Geliştirme Sunucusu (Flask)

```bash
flask run --host=0.0.0.0 --port=5000 --debug
```

Sunucu `http://localhost:5000` adresinde çalışacaktır.

### Redis Sunucusu

Redis'in arka planda çalıştığından emin olun. Varsayılan olarak `localhost:6379` portunu dinlemelidir.

## 7. Sorun Giderme

### `ModuleNotFoundError`
*   Sanal ortamın aktif olduğundan emin olun (`(venv)` ibaresini terminalde görmelisiniz).
*   `pip install -r requirements.txt` komutunu tekrar çalıştırın.

### `Redis Connection Error`
*   Redis sunucusunun çalıştığını kontrol edin.
*   `.env` dosyasındaki `REDIS_HOST` ve `REDIS_PORT` ayarlarını doğrulayın.

### CSS Yüklenmiyor / Görünmüyor
*   `npm run build:css` komutunu çalıştırarak CSS'in `static/css/tailwind.css` dizinine oluşturulduğundan emin olun.
