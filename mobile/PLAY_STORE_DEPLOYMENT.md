# 🚀 ORBIS - Google Play Store'a Yükleme Rehberi (DETAYLI)

## 📋 İÇİNDEKİLER

1. [Ön Hazırlık](#ön-hazırlık)
2. [Release APK/AAB Oluşturma](#release-apkaab-oluşturma)
3. [Google Play Console Kurulumu](#google-play-console-kurulumu)
4. [Uygulama Yükleme](#uygulama-yükleme)
5. [İnceleme ve Yayınlama](#inceleme-ve-yayınlama)
6. [Sorun Giderme](#sorun-giderme)

---

## 🎯 ÖN HAZIRLIK

### 1. Google Play Console Hesabı

- [Google Play Console](https://play.google.com/console) hesabı açın
- **Tek seferlik ücret:** $25 (kredi kartı gerekli)
- Geliştirici hesabı onayı: 1-2 gün

### 2. Gerekli Dosyalar Kontrolü

```bash
# Kontrol listesi
mobile/play-store/graphics/
  ✓ app-icon-512.png (512x512 px)
  ✓ feature-graphic.png (1024x500 px)
  ✓ screenshot-1-home.png
  ✓ screenshot-2-chart.png
  ✓ screenshot-3-ai.png

mobile/play-store/
  ✓ app-description-tr.txt
  ✓ app-description-en.txt
  ✓ privacy-policy.txt
  ✓ terms-of-service.txt
  ✓ data-safety.md
```

### 3. Web Sitesi Hazırlığı

Şu sayfaların CANLI olması gerekli:

- ✅ https://www.orbisastro.online/legal/privacy (Gizlilik Politikası)
- ✅ https://www.orbisastro.online/legal/terms (Kullanım Koşulları)
- ✅ https://www.orbisastro.online/legal/kvkk (KVKK)
- ✅ https://www.orbisastro.online (Ana sayfa)

---

## 🔨 RELEASE APK/AAB OLUŞTURMA

### ADIM 1: Keystore Oluştur (İlk Kez)

```bash
# Android Studio Terminal'de
cd D:\astro-ai-predictor\backend\flask_app\mobile\android\app

# Keystore oluştur
keytool -genkey -v -keystore orbis-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias orbis-key
```

**Sorulacak Bilgiler:**

- Şifre: `[GÜVENLİ BİR ŞİFRE - KAYDET!]`
- İsim: ORBIS
- Organizasyon: ORBIS
- Şehir: Istanbul
- Eyalet: Istanbul
- Ülke kodu: TR

**ÖNEMLİ:** Bu keystore dosyasını ve şifresini GÜVENLİ bir yerde sakla! Kaybedersen uygulamayı güncelleyemezsin!

### ADIM 2: Keystore Bilgilerini Ekle

`android/key.properties` dosyası oluştur:

```properties
storePassword=[KEYSTORE ŞİFRESİ]
keyPassword=[KEY ŞİFRESİ]
keyAlias=orbis-key
storeFile=app/orbis-release-key.jks
```

**ÖNEMLİ:** `key.properties` dosyasını `.gitignore`'a ekle!

### ADIM 3: build.gradle Güncelle

`android/app/build.gradle` dosyasına ekle:

```gradle
android {
    ...

    // Keystore config
    def keystorePropertiesFile = rootProject.file("key.properties")
    def keystoreProperties = new Properties()
    if (keystorePropertiesFile.exists()) {
        keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
    }

    signingConfigs {
        release {
            keyAlias keystoreProperties['keyAlias']
            keyPassword keystoreProperties['keyPassword']
            storeFile file(keystoreProperties['storeFile'])
            storePassword keystoreProperties['storePassword']
        }
    }

    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
}
```

### ADIM 4: Version Code ve Version Name Güncelle

`android/app/build.gradle`:

```gradle
android {
    defaultConfig {
        applicationId "com.orbis.astro"
        minSdkVersion 24
        targetSdkVersion 34
        versionCode 1        // Her yeni sürümde +1 artır
        versionName "1.0.0"  // Kullanıcıya gösterilen versiyon
    }
}
```

### ADIM 5: Release Build Oluştur

```bash
# Android Studio Terminal'de
cd D:\astro-ai-predictor\backend\flask_app\mobile\android

# Clean build
./gradlew clean

# AAB oluştur (Google Play için önerilen)
./gradlew bundleRelease

# VEYA APK oluştur
./gradlew assembleRelease
```

**Build Çıktıları:**

- AAB: `android/app/build/outputs/bundle/release/app-release.aab`
- APK: `android/app/build/outputs/apk/release/app-release.apk`

### ADIM 6: Build Kontrolü

```bash
# AAB boyutunu kontrol et (max 150 MB)
ls -lh android/app/build/outputs/bundle/release/app-release.aab

# APK boyutunu kontrol et
ls -lh android/app/build/outputs/apk/release/app-release.apk
```

---

## 🎮 GOOGLE PLAY CONSOLE KURULUMU

### ADIM 1: Uygulama Oluştur

1. [Google Play Console](https://play.google.com/console) → "Uygulama oluştur"
2. Bilgileri gir:
   - **Uygulama adı:** ORBIS - Kaderin Geometrisi
   - **Varsayılan dil:** Türkçe (Türkiye)
   - **Uygulama veya oyun:** Uygulama
   - **Ücretsiz veya ücretli:** Ücretsiz
3. Beyanları kabul et ve "Uygulama oluştur"

### ADIM 2: Mağaza Girişi (Store Listing)

**Konum:** Sol menü → Büyüme → Mağaza girişi → Ana mağaza girişi

#### 2.1 Uygulama Detayları

**Uygulama adı:**

```
ORBIS - Kaderin Geometrisi
```

**Kısa açıklama (80 karakter max):**

```
Yapay zeka destekli astroloji ve doğum haritası analizi uygulaması
```

**Tam açıklama (4000 karakter max):**
`mobile/play-store/app-description-tr.txt` dosyasındaki metni kopyala

#### 2.2 Grafikler

1. **Uygulama simgesi (512x512 px):**
   - `mobile/play-store/graphics/app-icon-512.png` yükle

2. **Özellik grafiği (1024x500 px):**
   - `mobile/play-store/graphics/feature-graphic.png` yükle

3. **Telefon ekran görüntüleri (minimum 2, maksimum 8):**
   - `screenshot-1-home.png`
   - `screenshot-2-chart.png`
   - `screenshot-3-ai.png`

#### 2.3 Kategori ve İletişim

- **Uygulama kategorisi:** Yaşam Tarzı
- **E-posta:** support@orbisastro.online
- **Telefon:** (opsiyonel)
- **Web sitesi:** https://www.orbisastro.online

### ADIM 3: Uygulama İçeriği (App Content)

**Konum:** Sol menü → Politika → Uygulama içeriği

#### 3.1 Gizlilik Politikası ✅

- URL: `https://www.orbisastro.online/legal/privacy`
- "Kaydet" butonuna tıkla

#### 3.2 Uygulama Erişimi ✅

- ✅ "Tüm işlevler kısıtlama olmadan kullanılabilir"
- "Kaydet" → "Gönder"

#### 3.3 Reklam ✅

- ✅ "Evet, uygulamam reklamlar içeriyor"
- Reklam türü: AdMob
- "Kaydet" → "Gönder"

#### 3.4 İçerik Derecelendirmesi ✅

Anketi doldur:

**Şiddet:**

- Gerçekçi şiddet: Hayır
- Fantastik şiddet: Hayır

**Cinsellik:**

- Cinsel içerik: Hayır
- Çıplaklık: Hayır

**Dil:**

- Küfür: Hayır
- Cinsel içerikli dil: Hayır

**Uyuşturucu:**

- Uyuşturucu referansı: Hayır

**Kumar:**

- Simüle kumar: Hayır
- Gerçek para kumar: Hayır

**Kullanıcı Etkileşimi:**

- Kullanıcı oluşturmalı içerik: Hayır
- Kullanıcılar birbirleriyle iletişim kurabilir: Hayır

**Sonuç:** PEGI 3 (3+ yaş)

#### 3.5 Hedef Kitle ve İçerik ✅

- **Hedef yaş grubu:** 13+ (çocuklara yönelik değil)
- "Kaydet" → "Gönder"

#### 3.6 Haberler Uygulaması ✅

- ❌ "Hayır, bu bir haberler uygulaması değil"

#### 3.7 COVID-19 İletişim Takibi ✅

- ❌ "Hayır"

#### 3.8 Veri Güvenliği ✅

**Veri toplama:**

- ✅ "Evet, bu uygulama kullanıcı verilerini toplar veya paylaşır"

**Toplanan veriler:**

1. **Kişisel Bilgiler:**
   - ✅ İsim (isteğe bağlı)
   - Toplama amacı: Uygulama işlevselliği
   - Paylaşılıyor mu: Hayır

2. **Konum:**
   - ✅ Yaklaşık konum
   - Toplama amacı: Uygulama işlevselliği (doğum yeri)
   - Paylaşılıyor mu: Hayır

3. **Uygulama Etkinliği:**
   - ✅ Uygulama etkileşimleri
   - Toplama amacı: Analitik
   - Paylaşılıyor mu: Evet (AdMob)

4. **Cihaz veya diğer kimlikler:**
   - ✅ Cihaz kimliği
   - Toplama amacı: Analitik, Reklam
   - Paylaşılıyor mu: Evet (AdMob)

**Güvenlik uygulamaları:**

- ✅ Veriler aktarım sırasında şifrelenir
- ✅ Kullanıcılar veri silme talebinde bulunabilir
- ✅ Veriler Google Play'in Aileler politikasına uygun

"Kaydet" → "Gönder"

#### 3.9 Hükümet Uygulaması ✅

- ❌ "Hayır"

#### 3.10 Finansal Özellikler ✅

- ❌ "Hayır" (IAP var ama finansal uygulama değil)

---

## 📦 UYGULAMA YÜKLEME

### ADIM 1: Üretim Sürümü Oluştur

**Konum:** Sol menü → Yayınla → Üretim

1. "Yeni sürüm oluştur" butonuna tıkla
2. "Google Play Uygulama İmzalama" seçeneğini kabul et (önerilen)

### ADIM 2: AAB/APK Yükle

1. "Yükle" butonuna tıkla
2. `android/app/build/outputs/bundle/release/app-release.aab` dosyasını seç
3. Yükleme tamamlanana kadar bekle

### ADIM 3: Sürüm Notları

**Türkçe (tr-TR):**

```
İlk sürüm! 🎉

✨ Özellikler:
• Yapay zeka destekli doğum haritası analizi
• Detaylı gezegen konumları ve evler
• Kişiselleştirilmiş AI yorumları
• Transit analizi ve öngörüler
• Vedik astroloji desteği
• Günlük, haftalık, aylık yorumlar

🌟 ORBIS ile kozmik yolculuğunuza başlayın!
```

### ADIM 4: İncelemeye Gönder

1. Tüm bilgileri kontrol et
2. "İncelemeye gönder" butonuna tıkla
3. Onay ver

---

## ⏳ İNCELEME VE YAYINLAMA

### İnceleme Süreci

- **İlk yükleme:** 1-7 gün (genelde 2-3 gün)
- **Güncellemeler:** 1-3 gün

### İnceleme Durumu

**Konum:** Sol menü → Yayınla → Üretim → Sürüm genel bakışı

**Durumlar:**

- 🟡 **İnceleniyor:** Google inceliyor
- 🟢 **Onaylandı:** Yayına hazır
- 🔴 **Reddedildi:** Sorun var, düzelt

### Yayınlama

Onaylandıktan sonra:

1. "Yayınla" butonuna tıkla
2. 1-2 saat içinde Play Store'da görünür

---

## 🔧 SORUN GİDERME

### Sık Karşılaşılan Sorunlar

#### 1. "Keystore şifresi yanlış"

```bash
# Keystore'u test et
keytool -list -v -keystore android/app/orbis-release-key.jks
```

#### 2. "Build başarısız"

```bash
# Cache temizle
cd android
./gradlew clean
./gradlew --stop

# Tekrar dene
./gradlew bundleRelease
```

#### 3. "Gizlilik politikası erişilemiyor"

- URL'nin HTTPS olduğundan emin ol
- Sayfanın 200 OK döndüğünü kontrol et
- Robots.txt'nin engellemediğini kontrol et

#### 4. "Veri güvenliği formu eksik"

- Tüm veri toplama türlerini belirt
- AdMob kullanıyorsan "Cihaz kimliği" ekle
- Konum kullanıyorsan "Yaklaşık konum" ekle

#### 5. "İçerik derecelendirmesi eksik"

- Anketi baştan sona doldur
- Tüm soruları cevapla
- "Gönder" butonuna tıkla

---

## 📊 YAYINLANDIKTAN SONRA

### 1. Play Console Dashboard

- **İndirmeler:** Günlük/haftalık/aylık
- **Derecelendirmeler:** Kullanıcı yorumları
- **Çökmeler:** Hata raporları
- **ANR'ler:** Uygulama yanıt vermiyor hataları

### 2. Güncelleme Yayınlama

```bash
# Version code'u artır (build.gradle)
versionCode 2
versionName "1.0.1"

# Yeni build oluştur
./gradlew bundleRelease

# Play Console'da yeni sürüm oluştur
# AAB'yi yükle
# Sürüm notlarını yaz
# İncelemeye gönder
```

### 3. Kullanıcı Geri Bildirimleri

- Yorumları düzenli kontrol et
- Sorunları hızlı çöz
- Pozitif yorumlara teşekkür et

---

## 📞 DESTEK

### Google Play Destek

- [Play Console Yardım](https://support.google.com/googleplay/android-developer)
- [Politika Merkezi](https://play.google.com/about/developer-content-policy/)

### ORBIS Destek

- E-posta: support@orbisastro.online
- Web: https://www.orbisastro.online

---

## ✅ CHECKLIST (Son Kontrol)

Yayınlamadan önce:

- [ ] Keystore güvenli yerde saklandı
- [ ] Version code ve version name güncellendi
- [ ] Release build başarıyla oluşturuldu
- [ ] Tüm görseller yüklendi (icon, feature graphic, screenshots)
- [ ] Mağaza açıklaması yazıldı
- [ ] Gizlilik politikası URL'si çalışıyor
- [ ] Uygulama içeriği formları dolduruldu
- [ ] Veri güvenliği formu tamamlandı
- [ ] İçerik derecelendirmesi alındı
- [ ] AAB/APK yüklendi
- [ ] Sürüm notları yazıldı
- [ ] İncelemeye gönderildi

---

**Son güncelleme:** 17 Ocak 2026

**Hazırlayan:** ORBIS Development Team

🚀 **Başarılar! Play Store'da görüşmek üzere!**
