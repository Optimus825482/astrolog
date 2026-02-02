"""
Abonelik Servisi
- Google Play Billing entegrasyonu
- Abonelik planları
"""
from datetime import datetime

class SubscriptionService:
    """Abonelik yönetimi"""
    
    PLANS = {
        "free": {
            "name": "Ücretsiz",
            "price": 0,
            "daily_interpretations": 0,  # Limit yok ama her işlem reklam gerektirir
            "requires_ad": True,  # Her işlem için reklam zorunlu
            "features": ["Reklam izleyerek analiz", "Reklam izleyerek AI yorum"]
        },
        "premium_daily": {
            "name": "Premium Günlük",
            "price": 30.0,  # TRY
            "google_product_id": "astro_premium_daily",
            "daily_interpretations": -1,  # Sınırsız
            "requires_ad": False,
            "features": [
                "Sınırsız analiz",
                "Sınırsız AI yorumu",
                "Reklamsız deneyim",
                "24 saat geçerli"
            ]
        },
        "premium_monthly": {
            "name": "Premium Aylık",
            "price": 49.99,  # TRY
            "google_product_id": "astro_premium_monthly",
            "daily_interpretations": -1,  # Sınırsız
            "features": [
                "Sınırsız AI yorumu",
                "Detaylı natal analiz",
                "Transit yorumları",
                "Uyumluluk analizi",
                "Reklamsız deneyim"
            ]
        },
        "premium_yearly": {
            "name": "Premium Yıllık",
            "price": 399.99,  # TRY (2 ay hediye)
            "google_product_id": "astro_premium_yearly",
            "daily_interpretations": -1,
            "features": [
                "Tüm premium özellikler",
                "2 ay hediye",
                "Öncelikli destek"
            ]
        }
    }
    
    def get_plans(self):
        """Tüm planları getir"""
        return self.PLANS
    
    def get_plan(self, plan_id: str):
        """Belirli planı getir"""
        return self.PLANS.get(plan_id)
