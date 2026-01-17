# ORBIS - Kaderin Geometrisi 🌌

**ORBIS**, astrolojik verileri modern yapay zeka analiziyle birleştiren, kullanıcı dostu ve premium tasarıma sahip bir **Progressive Web App (PWA)** platformudur.

---

## 🚀 Proje Amacı ve Vizyonu

Uygulama, karmaşık astroloji verilerini (gezegen konumları, açılar, evler) kullanıcıya estetik bir **geometrik düzen** içinde sunmayı ve AI yardımıyla bu verileri kişiselleştirilmiş hayat rehberliğine dönüştürmeyi hedefler. **"Kaderin Geometrisi"** mottosuyla, minimalizm ve yüksek teknolojiyi bir araya getirir.

---

## 🛠️ Teknik Mimari

### Backend (Flask Engine)

- **Framework:** Python Flask (Stateless & Serverless uyumlu).
- **Hesaplama:** `pyswisseph` (Swiss Ephemeris) kütüphanesi ile yüksek hassasiyetli gökyüzü haritası çıkartma.
- **AI Hub:** Google Gemini, DeepSeek ve OpenRouter API'leri üzerinden gelişmiş astrolojik yorumlama motoru.
- **Güvenlik:** Kullanıcı verileri sunucu tarafında saklanmaz; tüm süreçler dinamiktir.

### Frontend (Avant-Garde UI)

- **Tasarım Dili:** ORBIS Premium Design System (Stitch tabanlı).
- **Styling:** Tailwind CSS & Vanilla CSS (Glassmorphism, Neon Glow effects).
- **Interactions:** Alpine.js & JavaScript (Micro-interactions, 0.75x slow-motion Orb animations).
- **PWA Özellikleri:**
  - `manifest.json` ile telefona yüklenebilirlik.
  - `sw.js` (Service Worker) ile çevrimdışı önbellekleme.
  - Mobil-öncelikli Bottom Navigation Bar.

### Veri Yönetimi

- **LocalStorage:** Kullanıcı doğum bilgileri ve analiz geçmişi tamamen tarayıcı tarafında (Client-side) saklanır. Gizlilik en üst düzeydedir.

---

## ✨ Temel Özellikler

1.  **Kozmik Dashboard:** Tek bir ekrandan doğum ve transit bilgilerinin hızlıca girişi.
2.  **AI Analiz Hub:**
    - **Karakter:** Genel yaşam yolu ve ruhsal yapı analizi.
    - **Kariyer:** Mesleki potansiyeller ve finansal öngörüler.
    - **İlişkiler:** Aşk ve evlilik dinamikleri.
    - **Sesli Dinleme:** Analizlerin AI seslendirme (TTS) robotu ile dinlenebilmesi.
3.  **İnteraktif Harita:** Gezegenlerin burç ve ev konumlarının görselleştirilmesi.
4.  **Hızlı Paylaşım:** Kozmik raporların tek tuşla paylaşılabilmesi.

---

## 📂 Dosya Yapısı (Önemli Varlıklar)

- `/static/orb.mp4`: Uygulamanın kalbindeki merkezi enerji animasyonu.
- `/static/all-icons/`: PWA ve mobil cihazlar için tasarlanmış ikon seti.
- `/templates/layout.html`: Ana iskelet ve PWA navigasyon barı.
- `/templates/index.html`: Sinematik karşılama ekranı.
- `/templates/new_result.html`: Üç sekmeli (Özet, Harita, AI) sonuç merkezi.

---

## 🎯 Gelecek Hedefleri

- Sinastri (Aşk Uyumu) modülünün AI Hub'a eklenmesi.
- Daha detaylı gökyüzü transit takvim grafikleri.
- Bildirimler (Push Notifications) ile günlük astrolojik uyarılar.

---

_Bu doküman ORBIS projesinin temel yapısını ve vizyonunu özetlemek amacıyla oluşturulmuştur._ 🌌
