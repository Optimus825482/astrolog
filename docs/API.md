# 📡 API Referansı

Bu belge, frontend istemcileri (Web, Mobile) için mevcut olan RESTful endpoint'leri tanımlar.

---

## 1. Hesaplama Endpoint'leri

### `POST /results`
Astrolojik harita hesaplaması yapar.

*   **İçerik Tipi:** `application/x-www-form-urlencoded` (Form Post)
*   **Kullanım:** Web arayüzü ana formu.

**Parametreler:**

| İsim | Tip | Zorunlu | Açıklama |
|---|---|---|---|
| `birth_date` | Date | Evet | YYYY-MM-DD |
| `birth_time` | Time | Evet | HH:MM |
| `latitude` | Float | Evet | Enlem (örn: 41.0082) |
| `longitude` | Float | Evet | Boylam (örn: 28.9784) |
| `transit_date` | Date | Hayır | Transit tarihi |

---

## 2. AI Yorum Endpoint'leri

### `POST /api/get_ai_interpretation`
Hesaplanan harita verisine göre yapay zeka yorumu üretir.

*   **İçerik Tipi:** `application/json`

**İstek (Request):**

```json
{
  "interpretation_type": "daily",
  "user_name": "Ayşe Yılmaz",
  "astro_data": {
    "transit_to_natal_aspects": [
      {
        "planet1": "Mars",
        "aspect_type": "Square",
        "planet2": "Venus"
      }
    ]
  }
}
```

**Yanıt (Response):**

```json
{
  "success": true,
  "interpretation": "Bugün ilişkilerde gerginliklere dikkat etmelisiniz..."
}
```

**Hata Kodları:**
*   `500`: Sunucu hatası veya AI API erişim sorunu.
*   `429`: İstek limiti aşıldı (Rate limit).

---

## 3. Yardımcı Endpoint'ler

### `GET /search_location`
Şehir veya yer ismi arar.

*   **Parametre:** `query` (min 3 karakter)
*   **Örnek:** `/search_location?query=izmir`

**Yanıt:**

```json
{
  "locations": [
    {
      "name": "İzmir, Türkiye",
      "lat": 38.4237,
      "lng": 27.1428
    }
  ]
}
```

---

## 4. Kullanıcı Verileri

### `POST /api/delete-account`
Kullanıcı verilerini sistemden silme talebi (GDPR/KVKK).

**İstek:**
```json
{
  "user_id": "firebase_uid_12345"
}
```

**Yanıt:**
```json
{
  "success": true,
  "message": "Hesap silme talebi işleme alındı."
}
```
