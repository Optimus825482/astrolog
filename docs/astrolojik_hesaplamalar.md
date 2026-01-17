# Astrolojik Hesaplamalar ve İşlevleri

Bu belge, astrolojik hesaplamaları ve işlevlerini organize bir şekilde açıklar.

## 1. Natal Harita Hesaplamaları

### Temel Natal Hesaplamalar
| Hesaplama/Fonksiyon | Açıklama |
|---------------------|----------|
| **calculate_houses()** | Doğum tarihi, saati ve konuma göre astrolojik evleri hesaplar. Evler, hayatın farklı alanlarını temsil eder. |
| **calculate_natal_planet_positions()** | Doğum anındaki ana gezegen pozisyonlarını hesaplar (Güneş, Ay, Merkür vb.) |
| **calculate_natal_additional_points()** | Doğum anındaki ek noktaların (asteroidler, düğümler, Lilith vb.) pozisyonlarını hesaplar. |
| **calculate_aspects()** | Natal gezegenler arasındaki açıları hesaplar, doğum haritasındaki ilişkileri gösterir. |

### Natal Harita Detaylı Analizler
| Hesaplama/Fonksiyon | Açıklama |
|---------------------|----------|
| **get_natal_summary()** | Natal harita için özet bir yorum metni listesi oluşturur (temel karakter özellikleri). |
| **calculate_antiscia()** | Antiscia (karşıt dekan) ve contra-antiscia noktalarını hesaplar, gizli bağlantılar. |
| **calculate_dignity_scores()** | Gezegenlerin güç (yönetim, yücelim) veya zayıflık (düşüş, zarar) skorlarını hesaplar. |
| **get_midpoint_aspects()** | Gezegen çiftlerinin orta noktalarını ve bu noktaların açılarını hesaplar. |
| **calculate_lunation_cycle()** | Doğum anındaki Ay fazını hesaplar, temel duygusal yapıyı gösterir. |
| **calculate_declinations()** | Gezegenlerin ekliptik düzlemden sapma derecelerini hesaplar. |
| **calculate_fixed_stars()** | Sabit yıldızların pozisyonlarını hesaplar, kaderi etkileyen özel noktalar. |
| **calculate_part_of_fortune()** | Kişinin mutluluk ve şans noktasını hesaplar. |
| **calculate_arabic_parts()** | Arap noktalarını hesaplar, hayatın çeşitli alanlarını temsil eden özel noktalar. |
| **calculate_azimuth_altitude_for_bodies()** | Göksel cisimlerin ufuk üzerindeki konumlarını hesaplar. |

## 2. Transit Harita Hesaplamaları

### Temel Transit Hesaplamalar
| Hesaplama/Fonksiyon | Açıklama |
|---------------------|----------|
| **get_transit_positions()** | Belirli bir tarih için gezegen pozisyonlarını hesaplar, güncel etkiler. |
| **calculate_aspects()** | Transit gezegenler arasındaki açıları hesaplar (aynı fonksiyon farklı parametre ile). |

### Transit-Natal İlişki Hesaplamaları
| Hesaplama/Fonksiyon | Açıklama |
|---------------------|----------|
| **calculate_aspects()** | Transit ve natal pozisyonlar arasındaki açıları hesaplar, güncel etkileri gösterir. |

## 3. Progresyon ve Direk Hesaplamaları

| Hesaplama/Fonksiyon | Açıklama |
|---------------------|----------|
| **calculate_secondary_progressions()** | İkincil (sekonder) progresyonları hesaplar, kişisel gelişim süreçleri. |
| **get_solar_arc_progressions()** | Solar Arc progresyonlarını hesaplar, hayattaki önemli olaylar için. |
| **calculate_progressed_moon_phase()** | İlerletilmiş Ay fazını hesaplar, duygusal gelişim sürecini gösterir. |

## 4. Döngü ve Dönem Hesaplamaları

| Hesaplama/Fonksiyon | Açıklama |
|---------------------|----------|
| **calculate_solar_return_chart()** | Solar Return (Güneş dönüşü) haritasını hesaplar, yıllık astrolojik etkileri gösterir. |
| **calculate_lunar_return_chart()** | Lunar Return (Ay dönüşü) haritasını hesaplar, aylık duygusal etkileri gösterir. |
| **get_vimshottari_dasa()** | Hint astrolojisinde kullanılan Vimshottari Dasa periyotlarını hesaplar (yaşam dönemleri). |
| **get_firdaria_period()** | Ortaçağ astrolojisinde kullanılan Firdaria periyotlarını hesaplar (hayat aşamaları). |
| **find_eclipses_in_range()** | Belirli bir tarih aralığında Güneş ve Ay tutulmalarını bulur, önemli dönüm noktaları. |

## 5. Harmonik Analiz Hesaplamaları

| Hesaplama/Fonksiyon | Açıklama |
|---------------------|----------|
| **get_harmonic_chart()** | Belirli bir harmonik sayısı için harita hesaplaması yapar. |
| **calculate_deep_harmonic_analysis()** | Birden çok harmonik haritayı hesaplar (evlilik, kariyer, ruhsal gelişim vb. alanlar). |

## 6. Ana Hesaplama Fonksiyonu

| Hesaplama/Fonksiyon | Açıklama |
|---------------------|----------|
| **calculate_astro_data()** | Tüm astrolojik hesaplamaları bir araya getirir, kapsamlı doğum haritası ve analiz oluşturur. |
| **calculate_celestial_positions()** | Gezegenlerin ve göksel cisimlerin pozisyonlarını hesaplayan temel fonksiyon (diğer fonksiyonlar tarafından kullanılır). |

## Astrolojik Haritada Temel Bileşenler

| Bileşen | Astrolojik Anlamı |
|---------|-------------------|
| **Gezegenler** | Kişiliğin farklı yönlerini ve yaşam enerjilerini temsil eder. |
| **Burçlar** | Gezegenlerin enerjilerinin nasıl ifade edildiğini gösterir. |
| **Evler** | Bu enerjilerin hayatın hangi alanlarında aktif olduğunu gösterir. |
| **Açılar** | Gezegenler arasındaki ilişkileri ve enerjilerin nasıl etkileştiğini gösterir. |
| **Yükselen (Ascendant)** | Kişinin dış dünyaya yansıttığı imajı ve fiziksel özellikleri gösterir. |
| **MC (Midheaven)** | Kariyer, sosyal statü ve hayat amacını gösterir. |
| **Düğümler** | Karmik yönü ve ruhsal gelişim yolunu gösterir. |
| **Harmonikler** | Kişiliğin ve yaşamın farklı katmanlarını açığa çıkarır. |
| **Progresyonlar** | Kişisel gelişim sürecini ve zamanla ortaya çıkan özellikleri gösterir. |
| **Transitler** | Güncel gezegen hareketlerinin doğum haritasıyla etkileşimini gösterir, günlük etkiler. |

## Hesaplama Akış Şeması (Önerilen)

1. **Natal Harita Hesaplamaları**:
   - Evleri hesapla (calculate_houses)
   - Natal gezegen pozisyonlarını hesapla (calculate_natal_planet_positions)
   - Natal ek noktaları hesapla (calculate_natal_additional_points)
   - Natal açıları hesapla (calculate_aspects - natal pozisyonlar arası)
   - Natal harita detaylarını hesapla (dignity_scores, antiscia, midpoints, vb.)

2. **Transit Harita Hesaplamaları**:
   - Transit evleri hesapla (calculate_houses - transit tarih için)
   - Transit gezegen pozisyonlarını hesapla (get_transit_positions)
   - Transit açıları hesapla (calculate_aspects - transit pozisyonlar arası)

3. **Transit-Natal İlişki Hesaplamaları**:
   - Transit-Natal açıları hesapla (calculate_aspects - transit ve natal pozisyonlar arası)

4. **Ek Hesaplamalar**:
   - Progresyonlar, Dönüşler, Harmonikler, Dönemler vb. 