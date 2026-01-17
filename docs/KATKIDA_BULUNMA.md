# 🤝 Katkıda Bulunma Rehberi

Astro AI Predictor'a katkıda bulunmak istediğiniz için teşekkürler! Bu rehber, kod standartlarımızı ve geliştirme akışımızı açıklar.

## Geliştirme Akışı (Workflow)

1.  **Issue Seçimi:** Yapılacak işi belirleyin veya yeni bir Issue açın.
2.  **Branch Açma:** Ana daldan (`main`) yeni bir dal oluşturun.
    *   İsimlendirme: `feature/ozellik-adi` veya `fix/hata-adi`.
3.  **Geliştirme:** Kodunuzu yazın.
4.  **Test:** Yerel testleri çalıştırın.
5.  **Pull Request:** Değişikliklerinizi gönderin.

## Kod Standartları

*   **PEP 8:** Python kodu PEP 8 standartlarına uygun olmalıdır.
*   **Tip Güvenliği:** `typing` modülü kullanılarak fonksiyon imzalarına tip ipuçları (type hints) eklenmelidir.
*   **Docstrings:** Her fonksiyon ve sınıfın ne işe yaradığını, parametrelerini ve dönüş değerini açıklayan docstring'i olmalıdır.

**Örnek:**

```python
def calculate_aspect(planet1: dict, planet2: dict) -> Optional[dict]:
    """
    İki gezegen arasındaki açıyı hesaplar.

    Args:
        planet1: Birinci gezegen verisi.
        planet2: İkinci gezegen verisi.

    Returns:
        Açı detayları veya None.
    """
    # ...
```

## Testler

Proje `pytest` kullanır. Her yeni özellik için test yazılması zorunludur.

Testleri çalıştırmak için:

```bash
# Tüm testler
pytest

# Sadece entegrasyon testleri
pytest tests/integration/
```

## Commit Mesajları

*   Açık ve emir kipinde yazın: "Fix login bug" yerine "Fixed login bug" değil, **"Fix login bug"**.
*   Mümkünse konuyu önek olarak ekleyin: `[AI] Update prompts`, `[UI] Fix button color`.

---
Topluluğumuzun bir parçası olduğunuz için mutluyuz!
