# 🎯 Android Studio ile Release Build ve Keystore Oluşturma

## 📋 ADIM ADIM REHBER

### ADIM 1: Android Studio'yu Aç

1. **Android Studio'yu başlat**
2. **File → Open**
3. Şu klasörü seç: `D:\astro-ai-predictor\backend\flask_app\mobile\android`
4. **OK** butonuna tıkla
5. Gradle sync tamamlanana kadar bekle (1-2 dakika)

---

### ADIM 2: Build Variant'ı Release Yap

1. Sol altta **Build Variants** sekmesine tıkla
2. **app** modülü için **release** seç (varsayılan: debug)

![Build Variants](https://i.imgur.com/example.png)

---

### ADIM 3: Signed Bundle/APK Oluştur

1. Üst menüden **Build → Generate Signed Bundle / APK** seç
2. **Android App Bundle** seçeneğini işaretle (AAB - Google Play için önerilen)
3. **Next** butonuna tıkla

---

### ADIM 4: Keystore Oluştur (İLK KEZ)

#### 4.1 Create New Keystore

1. **Create new...** butonuna tıkla
2. Keystore bilgilerini gir:

**Key store path:**

```
D:\astro-ai-predictor\backend\flask_app\mobile\android\app\orbis-release-key.jks
```

**Password:**

```
[GÜÇLÜ BİR ŞİFRE - EN AZ 6 KARAKTER]
```

**⚠️ ÖNEMLİ:** Bu şifreyi bir yere yaz! Kaybedersen uygulamayı güncelleyemezsin!

**Confirm:**

```
[AYNI ŞİFREYİ TEKRAR GİR]
```

#### 4.2 Key Bilgileri

**Alias:**

```
orbis-key
```

**Password:**

```
[AYNI ŞİFRE VEYA FARKLI BİR ŞİFRE]
```

**Validity (years):**

```
25
```

(Varsayılan 25 yıl - değiştirme)

#### 4.3 Certificate Bilgileri

**First and Last Name:**

```
ORBIS
```

**Organizational Unit:**

```
ORBIS Development
```

**Organization:**

```
ORBIS
```

**City or Locality:**

```
Istanbul
```

**State or Province:**

```
Istanbul
```

**Country Code (XX):**

```
TR
```

#### 4.4 Oluştur

1. Tüm bilgileri kontrol et
2. **OK** butonuna tıkla
3. Keystore oluşturuldu! ✅

---

### ADIM 5: Build Ayarları

1. **Key store path:** Otomatik dolduruldu ✅
2. **Key store password:** Şifreni gir
3. **Key alias:** `orbis-key` (otomatik)
4. **Key password:** Şifreni gir
5. **Remember passwords** işaretleyebilirsin (opsiyonel)
6. **Next** butonuna tıkla

---

### ADIM 6: Build Variant Seç

1. **release** seçili olmalı ✅
2. **Signature Versions:**
   - ✅ **V1 (Jar Signature)** işaretle
   - ✅ **V2 (Full APK Signature)** işaretle
3. **Finish** butonuna tıkla

---

### ADIM 7: Build Süreci

1. Build başladı! ⏳
2. Alt kısımda **Build** sekmesinde ilerlemeyi izle
3. Süre: 2-5 dakika
4. Tamamlandığında: **locate** linki görünür

---

### ADIM 8: AAB Dosyasını Bul

**Çıktı konumu:**

```
D:\astro-ai-predictor\backend\flask_app\mobile\android\app\build\outputs\bundle\release\app-release.aab
```

**Dosya boyutu:** ~15-30 MB (normal)

---

## ✅ BAŞARILI! ŞİMDİ NE YAPACAKSIN?

### 1. Keystore'u Yedekle

**ÇOK ÖNEMLİ:** Bu dosyaları güvenli bir yere kopyala:

```
D:\astro-ai-predictor\backend\flask_app\mobile\android\app\orbis-release-key.jks
```

**Şifreleri kaydet:**

- Keystore password: [ŞIFREN]
- Key password: [ŞIFREN]
- Key alias: orbis-key

**Yedekleme yerleri:**

- ✅ USB bellek
- ✅ Google Drive (şifreli)
- ✅ Dropbox (şifreli)
- ✅ Harici disk

**⚠️ UYARI:** Bu keystore'u kaybedersen uygulamayı ASLA güncelleyemezsin!

### 2. AAB'yi Google Play Console'a Yükle

1. [Google Play Console](https://play.google.com/console) aç
2. Uygulamayı oluştur (henüz oluşturmadıysan)
3. **Yayınla → Üretim → Yeni sürüm oluştur**
4. `app-release.aab` dosyasını yükle
5. Sürüm notlarını yaz
6. **İncelemeye gönder**

---

## 🔄 SONRAKI GÜNCELLEMELER İÇİN

### Keystore Zaten Var (2. kez build)

1. **Build → Generate Signed Bundle / APK**
2. **Android App Bundle** → Next
3. **Choose existing...** butonuna tıkla
4. `orbis-release-key.jks` dosyasını seç
5. Şifreleri gir
6. **Next → Finish**

### Version Code Güncelle

Her yeni sürüm için `android/app/build.gradle`:

```gradle
android {
    defaultConfig {
        versionCode 2        // +1 artır (1 → 2 → 3 ...)
        versionName "1.0.1"  // Kullanıcıya gösterilen (1.0.0 → 1.0.1)
    }
}
```

---

## 🐛 SORUN GİDERME

### "Gradle sync failed"

```bash
# Terminal'de
cd D:\astro-ai-predictor\backend\flask_app\mobile\android
./gradlew clean
```

Sonra Android Studio'da: **File → Sync Project with Gradle Files**

### "Build failed"

1. **Build → Clean Project**
2. **Build → Rebuild Project**
3. Tekrar dene

### "Keystore was tampered with"

Şifre yanlış! Doğru şifreyi gir.

### "Duplicate resources"

`android/app/build.gradle`:

```gradle
android {
    packagingOptions {
        exclude 'META-INF/DEPENDENCIES'
        exclude 'META-INF/LICENSE'
        exclude 'META-INF/LICENSE.txt'
        exclude 'META-INF/NOTICE'
        exclude 'META-INF/NOTICE.txt'
    }
}
```

---

## 📊 BUILD ÇIKTILARI

### AAB (Android App Bundle) - Google Play için

**Konum:**

```
android/app/build/outputs/bundle/release/app-release.aab
```

**Kullanım:** Google Play Console'a yükle

### APK (Android Package) - Test için

Eğer APK istersen:

1. **Build → Generate Signed Bundle / APK**
2. **APK** seç (AAB yerine)
3. Aynı adımları takip et

**Konum:**

```
android/app/build/outputs/apk/release/app-release.apk
```

**Kullanım:** Cihaza direkt yükle (test için)

---

## 🎯 CHECKLIST

Build öncesi kontrol:

- [ ] Android Studio açık
- [ ] `mobile/android` projesi yüklü
- [ ] Gradle sync tamamlandı
- [ ] Build variant: **release**
- [ ] Version code güncellendi (2. build ise)
- [ ] Version name güncellendi (2. build ise)

Build sonrası kontrol:

- [ ] AAB dosyası oluşturuldu
- [ ] Dosya boyutu normal (15-30 MB)
- [ ] Keystore yedeklendi
- [ ] Şifreler kaydedildi

---

## 📞 YARDIM

Sorun yaşarsan:

1. **Build → Clean Project**
2. **File → Invalidate Caches / Restart**
3. Android Studio'yu yeniden başlat
4. Tekrar dene

Hala sorun varsa: `mobile/PLAY_STORE_DEPLOYMENT.md` → Sorun Giderme bölümü

---

**Hazırladı:** ORBIS Development Team  
**Son güncelleme:** 17 Ocak 2026

🚀 **Başarılar!**
