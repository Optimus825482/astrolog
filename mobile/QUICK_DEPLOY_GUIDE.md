# ⚡ ORBIS - Play Store Hızlı Yükleme Rehberi

## 🎯 5 ADIMDA PLAY STORE'A YÜKLE

### ADIM 1: Keystore Oluştur (5 dakika)

```bash
cd D:\astro-ai-predictor\backend\flask_app\mobile\android\app

keytool -genkey -v -keystore orbis-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias orbis-key
```

**Şifre belirle ve KAYDET!** (Bu şifreyi kaybedersen uygulamayı güncelleyemezsin!)

### ADIM 2: key.properties Oluştur

`android/key.properties` dosyası oluştur:

```properties
storePassword=SENIN_SIFREN
keyPassword=SENIN_SIFREN
keyAlias=orbis-key
storeFile=app/orbis-release-key.jks
```

### ADIM 3: Release Build Oluştur (10 dakika)

```bash
cd D:\astro-ai-predictor\backend\flask_app\mobile\android

# Clean
./gradlew clean

# AAB oluştur
./gradlew bundleRelease
```

**Çıktı:** `android/app/build/outputs/bundle/release/app-release.aab`

### ADIM 4: Google Play Console Kurulumu (30 dakika)

1. [Google Play Console](https://play.google.com/console) → Uygulama oluştur
2. **Mağaza Girişi:**
   - Uygulama adı: ORBIS - Kaderin Geometrisi
   - Kısa açıklama: `mobile/play-store/app-description-tr.txt` (ilk 80 karakter)
   - Tam açıklama: `mobile/play-store/app-description-tr.txt` (tamamı)
   - Görseller: `mobile/play-store/graphics/` klasöründen yükle
3. **Uygulama İçeriği:**
   - Gizlilik politikası: https://www.orbisastro.online/legal/privacy
   - Reklam: Evet (AdMob)
   - İçerik derecelendirmesi: Anketi doldur → PEGI 3
   - Hedef kitle: 13+
   - Veri güvenliği: `mobile/play-store/data-safety.md` referans al

### ADIM 5: AAB Yükle ve Yayınla (5 dakika)

1. Sol menü → Yayınla → Üretim
2. "Yeni sürüm oluştur"
3. `app-release.aab` dosyasını yükle
4. Sürüm notları yaz
5. "İncelemeye gönder"

---

## ⏳ BEKLEME SÜRELERİ

- **Google Play hesabı onayı:** 1-2 gün
- **İlk uygulama incelemesi:** 2-7 gün
- **Güncellemeler:** 1-3 gün

---

## 🆘 HIZLI YARDIM

### Build Hatası?

```bash
cd android
./gradlew clean
./gradlew --stop
./gradlew bundleRelease
```

### Keystore Şifresi Unutuldu?

❌ **Çözüm yok!** Yeni keystore oluştur, yeni uygulama olarak yükle.

### İnceleme Reddedildi?

1. Play Console'da ret nedenini oku
2. Sorunu düzelt
3. Yeni sürüm oluştur
4. Tekrar gönder

---

## 📚 DETAYLI REHBER

Daha fazla bilgi için: `mobile/PLAY_STORE_DEPLOYMENT.md`

---

**Başarılar! 🚀**
