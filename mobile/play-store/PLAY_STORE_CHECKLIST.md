# 🚀 ORBIS - Google Play Store Yükleme Rehberi

## ✅ Hazır Materyaller

### 1. Görseller (graphics/ klasöründe)

| Dosya                    | Boyut       | Kullanım                       |
| ------------------------ | ----------- | ------------------------------ |
| `app-icon-512.png`       | 512x512 px  | Mağaza ikonu                   |
| `feature-graphic.png`    | 1024x500 px | Tanıtım banner'ı               |
| `screenshot-1-home.png`  | Telefon     | Ana sayfa ekran görüntüsü      |
| `screenshot-2-chart.png` | Telefon     | Doğum haritası ekran görüntüsü |
| `screenshot-3-ai.png`    | Telefon     | AI yorum ekran görüntüsü       |

### 2. Metin İçerikleri

| Dosya                    | Açıklama                      |
| ------------------------ | ----------------------------- |
| `app-description-tr.txt` | Türkçe mağaza açıklaması      |
| `app-description-en.txt` | İngilizce mağaza açıklaması   |
| `privacy-policy.txt`     | Gizlilik politikası           |
| `terms-of-service.txt`   | Kullanım koşulları            |
| `data-safety.md`         | Veri güvenliği form bilgileri |

---

## 📋 Play Console Adımları

### ADIM 1: Uygulama Oluştur

1. [Google Play Console](https://play.google.com/console) açın
2. "Uygulama oluştur" butonuna tıklayın
3. Bilgileri girin:
   - **Uygulama adı:** ORBIS - Kaderin Geometrisi
   - **Varsayılan dil:** Türkçe
   - **Uygulama türü:** Uygulama
   - **Ücretsiz/Ücretli:** Ücretsiz
   - Beyanları kabul edin

### ADIM 2: Mağaza Girişi (Store Listing)

**Konum:** Büyüme > Mağaza girişi > Ana mağaza girişi

1. **Kısa açıklama (80 karakter):**

```
Yapay zeka destekli astroloji ve doğum haritası analizi uygulaması
```

2. **Tam açıklama:**
   `app-description-tr.txt` dosyasındaki metni kopyalayın

3. **Uygulama simgesi:**
   `graphics/app-icon-512.png` dosyasını yükleyin

4. **Özellik grafiği:**
   `graphics/feature-graphic.png` dosyasını yükleyin

5. **Ekran görüntüleri (minimum 2 adet):**

- `graphics/screenshot-1-home.png`
- `graphics/screenshot-2-chart.png`
- `graphics/screenshot-3-ai.png`

### ADIM 3: Uygulama İçeriği (App Content)

**Konum:** Politika > Uygulama içeriği

#### 3.1 Gizlilik Politikası

- URL: `https://www.orbisastro.online/legal/privacy`

#### 3.2 Reklam

- ✅ "Evet, reklamlar içeriyor" seçin
- AdMob kullanıyoruz

#### 3.3 Uygulama Erişimi

- ✅ "Tüm işlevler kısıtlama olmadan kullanılabilir" seçin

#### 3.4 İçerik Derecelendirmesi

Anket sorularına cevaplar:

- Şiddet: Hayır
- Cinsellik: Hayır
- Kumar: Hayır
- Uyuşturucu: Hayır
- Kullanıcı oluşturmalı içerik: Hayır
- **Sonuç: 3+ yaş (PEGI 3)**

#### 3.5 Hedef Kitle

- ✅ 13+ yaş (çocuklara yönelik değil)

#### 3.6 Veri Güvenliği

`data-safety.md` dosyasını referans alarak formu doldurun:

- ✅ Veri topluyoruz
- ✅ Veri şifreleniyor
- ✅ Kullanıcı silme talep edebilir
- Toplanan veriler: İsim (isteğe bağlı), doğum bilgileri, yaklaşık konum, cihaz kimliği
- Paylaşılan veriler: AdMob için cihaz kimliği

### ADIM 4: APK/AAB Yükleme

**Konum:** Yayınla > Üretim

1. Android Studio'da Release APK/AAB oluşturun:

```bash
cd D:\astro-ai-predictor\backend\flask_app\mobile\android
./gradlew bundleRelease
```

2. APK konumu:

```
android/app/build/outputs/bundle/release/app-release.aab
```

3. Play Console'da "Yeni sürüm" oluşturun
4. AAB dosyasını yükleyin

### ADIM 5: Uygulama İmzalama

- Google tarafından yönetilen imzalama kullanın (önerilen)
- Veya kendi keystore'unuzu yükleyin

---

## 🔗 Önemli Linkler

| Sayfa               | URL                                         |
| ------------------- | ------------------------------------------- |
| Gizlilik Politikası | https://www.orbisastro.online/legal/privacy |
| Kullanım Koşulları  | https://www.orbisastro.online/legal/terms   |
| KVKK                | https://www.orbisastro.online/legal/kvkk    |
| Çerez Politikası    | https://www.orbisastro.online/legal/cookies |
| Web Sitesi          | https://www.orbisastro.online               |

---

## 📧 İletişim Bilgileri

- **Geliştirici:** ORBIS
- **E-posta:** support@orbis.app
- **Privacy:** privacy@orbis.app
- **Website:** https://www.orbisastro.online

---

## ⚠️ Önemli Notlar

1. **APK İmzalama:** Release build için keystore dosyası gerekli
2. **AdMob App ID:** AndroidManifest.xml'de doğru olduğundan emin olun
3. **Minimum SDK:** 24 (Android 7.0)
4. **Target SDK:** 34 (Android 14)
5. **İnceleme Süresi:** İlk yükleme 1-3 gün sürebilir

---

Son güncelleme: 15 Ocak 2026
