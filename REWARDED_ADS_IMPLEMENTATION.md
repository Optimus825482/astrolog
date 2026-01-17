# ORBIS Rewarded Ads Implementation - YENİ STRATEJİ

## 🎯 Monetizasyon Stratejisi

### Ücretsiz Kullanıcılar:

- **Günlük 3 reklam izleme hakkı**
- Her analiz için **rewarded ad izleme ZORUNLU**
- Her AI yorum için **rewarded ad izleme ZORUNLU**
- 3 reklam sonrası **Premium zorunlu**

### Premium Günlük (30 TL):

- **Sınırsız** analiz
- **Sınırsız** AI yorum
- **Reklamsız** deneyim
- **Öncelikli** AI yanıtları

## 📱 İlk Açılış (Onboarding)

### Dosya: `templates/components/premium_onboarding_modal.html`

- İlk açılışta Premium teklifi gösterilir
- Ücretsiz plan özellikleri açıklanır
- Premium avantajları vurgulanır
- "Ücretsiz Devam Et" butonu ile kapatılabilir

### Kontrol:

```javascript
// localStorage'da 'orbis_seen_onboarding' kontrolü
// İlk açılışta modal gösterilir
```

## 🎬 Rewarded Ad Sistemi

### Dosya: `mobile/www/js/rewarded-ads.js`

#### Fonksiyonlar:

1. **`showForAnalysis()`** - Analiz öncesi reklam
2. **`showForInterpretation()`** - AI yorum öncesi reklam

#### Kullanım:

```javascript
// Analiz öncesi
const rewarded = await window.OrbisRewardedAds.showForAnalysis();
if (rewarded) {
  // Analiz yap
} else {
  // Reklam izlenmedi, Premium öner
}

// AI yorum öncesi
const rewarded = await window.OrbisRewardedAds.showForInterpretation();
if (rewarded) {
  // Yorum göster
} else {
  // Reklam izlenmedi, Premium öner
}
```

## 🔧 Backend Değişiklikleri

### Dosya: `monetization/usage_tracker.py`

#### Yeni Parametreler:

```python
FREE_DAILY_LIMIT = 3  # Günlük reklam izleme limiti
PREMIUM_DAILY_PRICE = 30.0  # TRY
```

#### Yeni Fonksiyon:

```python
def can_use_feature(device_id, feature="ad_watch", email=None):
    """
    Returns:
    {
        "allowed": True/False,
        "requires_ad": True/False,  # Reklam izleme gerekli mi
        "remaining": int,  # Kalan hak
        "premium_price": 30.0
    }
    """
```

## 📝 Entegrasyon Adımları

### 1. Dashboard (Analiz Butonu)

```javascript
// templates/dashboard.html - submitForm() fonksiyonunda

async function submitForm() {
  // Kullanım kontrolü
  const usage = await checkUsage();

  if (!usage.allowed) {
    showPremiumModal();
    return;
  }

  if (usage.requires_ad) {
    // Rewarded ad göster
    const rewarded = await window.OrbisRewardedAds.showForAnalysis();
    if (!rewarded) {
      alert("Analiz yapmak için reklam izlemeniz gerekiyor!");
      return;
    }

    // Kullanımı kaydet
    await recordAdWatch();
  }

  // Formu gönder
  document.getElementById("orbisForm").submit();
}
```

### 2. AI Yorum (interpretTab fonksiyonu)

```javascript
// templates/new_result.html - interpretTab() fonksiyonunda

async function interpretTab(tabId) {
  // Kullanım kontrolü
  const usage = await checkUsage();

  if (!usage.allowed) {
    showPremiumModal();
    return;
  }

  if (usage.requires_ad) {
    // Rewarded ad göster
    const rewarded = await window.OrbisRewardedAds.showForInterpretation();
    if (!rewarded) {
      alert("AI yorum okumak için reklam izlemeniz gerekiyor!");
      return;
    }

    // Kullanımı kaydet
    await recordAdWatch();
  }

  // AI yorumu yükle
  loadAIInterpretation(tabId);
}
```

### 3. Backend API

```python
# routes/main.py

@app.route('/api/check_usage', methods=['POST'])
def check_usage():
    device_id = request.json.get('device_id')
    email = request.json.get('email')

    tracker = UsageTracker()
    usage = tracker.can_use_feature(device_id, 'ad_watch', email)

    return jsonify(usage)

@app.route('/api/record_ad_watch', methods=['POST'])
def record_ad_watch():
    device_id = request.json.get('device_id')
    email = request.json.get('email')

    tracker = UsageTracker()
    result = tracker.record_usage(device_id, 'ad_watch', email)

    return jsonify(result)
```

## 🎨 UI/UX Akışı

### Senaryo 1: İlk Kullanıcı

1. Uygulama açılır
2. **Onboarding modal** gösterilir (Premium teklifi)
3. "Ücretsiz Devam Et" seçilir
4. Dashboard açılır
5. Analiz butonu tıklanır
6. **Rewarded ad** gösterilir
7. Reklam izlenir
8. Analiz yapılır (1/3 hak kullanıldı)

### Senaryo 2: 3. Reklam Sonrası

1. 3. analiz/yorum için reklam izlenir
2. Limit doldu mesajı gösterilir
3. **Premium modal** açılır
4. "Premium'a Geç - 30 TL" butonu
5. IAP ile satın alma
6. Premium aktif, sınırsız kullanım

### Senaryo 3: Premium Kullanıcı

1. Premium aktif
2. Hiç reklam gösterilmez
3. Sınırsız analiz + yorum
4. Öncelikli AI yanıtları

## 🚀 Deployment Checklist

- [ ] `mobile/www/js/rewarded-ads.js` eklendi
- [ ] `templates/components/premium_onboarding_modal.html` oluşturuldu
- [ ] `templates/layout.html` - onboarding modal include edildi
- [ ] `templates/dashboard.html` - submitForm() rewarded ad eklendi
- [ ] `templates/new_result.html` - interpretTab() rewarded ad eklendi
- [ ] `monetization/usage_tracker.py` - yeni strateji uygulandı
- [ ] `routes/main.py` - API endpoint'leri eklendi
- [ ] `mobile/www/index.html` - rewarded-ads.js script eklendi
- [ ] AdMob Rewarded Ad Unit ID güncellendi
- [ ] Google Play IAP - `astro_premium_daily` product ID eklendi
- [ ] Vercel deploy
- [ ] Android Studio test

## 💰 IAP Product IDs

```javascript
// mobile/www/js/iap.js

const PRODUCTS = {
  PREMIUM_DAILY: {
    id: "astro_premium_daily",
    type: "subscription",
    price: "30 TL",
    duration: "1 gün",
  },
};
```

## 📊 Analytics Events

```javascript
// Reklam izleme
gtag("event", "rewarded_ad_watched", {
  purpose: "analysis" | "interpretation",
  remaining_quota: 2,
});

// Premium satın alma
gtag("event", "purchase", {
  transaction_id: "xxx",
  value: 30,
  currency: "TRY",
  items: [
    {
      item_id: "astro_premium_daily",
      item_name: "Premium Günlük",
    },
  ],
});
```

## ⚠️ Önemli Notlar

1. **Rewarded Ad Unit ID** - AdMob'da oluşturulmalı
2. **IAP Product ID** - Google Play Console'da tanımlanmalı
3. **Test Mode** - Geliştirme sırasında `isTesting: true`
4. **Fallback** - Reklam yüklenemezse kullanıcıya izin ver (test için)
5. **Admin Bypass** - Admin kullanıcılar reklam görmez

---

**Son Güncelleme:** 2026-01-17
**Durum:** Implementation Ready
