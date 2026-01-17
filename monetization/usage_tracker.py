"""
Kullanım Takip Sistemi - YENİ STRATEJİ
- Günlük 3 ücretsiz REKLAM İZLEME (analiz + yorum için)
- Her analiz için rewarded ad izleme ZORUNLU
- Her AI yorum için rewarded ad izleme ZORUNLU
- 3 reklam sonrası Premium zorunlu
- Premium Günlük: 30 TL (sınırsız analiz + yorum + reklamsız)
- Supabase entegrasyonu (production)
"""
from datetime import datetime, date, timedelta
from flask import current_app
import json
import os
from typing import Optional, Dict, Any

# Admin email listesi - bu kullanıcılar her zaman premium gibi davranır
ADMIN_EMAILS = os.environ.get('ADMIN_EMAILS', '').split(',')
# Admin email'lerini normalize et (boşlukları temizle, küçük harfe çevir)
ADMIN_EMAILS = [email.strip().lower() for email in ADMIN_EMAILS if email.strip()]

class UsageTracker:
    """Kullanıcı kullanım takibi - Günlük reklam izleme limiti"""
    
    FREE_DAILY_LIMIT = 3  # Günlük ücretsiz REKLAM İZLEME sayısı
    PREMIUM_DAILY_PRICE = 30.0  # TRY
    
    # In-memory storage (fallback)
    _memory_storage = {}
    
    def __init__(self, storage_path=None, use_supabase=True):
        self.storage_path = storage_path or "instance/usage_data.json"
        self.use_supabase = use_supabase and self._init_supabase()
        self.use_memory = not self.use_supabase
        
        # Local development için file storage dene
        if not self.use_supabase:
            try:
                self._ensure_storage()
            except:
                self.use_memory = True
    
    def _init_supabase(self) -> bool:
        """Supabase bağlantısını başlat"""
        try:
            from services.firebase_service import firebase_service
            if firebase_service and firebase_service.db:
                self.db = firebase_service.db
                return True
        except Exception as e:
            print(f"[UsageTracker] Supabase init hatası: {e}")
        return False
    
    def _ensure_storage(self):
        """Storage dosyasını oluştur (sadece local)"""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            if not os.path.exists(self.storage_path):
                with open(self.storage_path, 'w') as f:
                    json.dump({}, f)
        except:
            self.use_memory = True
    
    def _load_data(self):
        """Veriyi yükle (Supabase, memory veya file)"""
        if self.use_supabase:
            return {}  # Supabase'de her sorgu direkt DB'den gelir
        if self.use_memory:
            return self._memory_storage
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def _save_data(self, data):
        """Veriyi kaydet (Supabase, memory veya file)"""
        if self.use_supabase:
            return  # Supabase'de her kayıt direkt DB'ye yazılır
        if self.use_memory:
            self._memory_storage = data
        else:
            try:
                with open(self.storage_path, 'w') as f:
                    json.dump(data, f, indent=2)
            except:
                self._memory_storage = data
    def get_user_usage(self, device_id: str, email: str = None) -> dict:
        """Kullanıcının bugünkü kullanımını getir"""
        today = date.today().isoformat()
        
        print(f"[UsageTracker] 🔍 get_user_usage - device_id: {device_id}, email: {email}, today: {today}")
        
        # Supabase'den oku
        if self.use_supabase:
            try:
                doc = self.db.collection('usage_tracking').document(device_id).get()
                if doc.exists:
                    user_data = doc.to_dict()
                    print(f"[UsageTracker] ✅ Supabase - User found: {user_data}")
                else:
                    # Yeni kullanıcı oluştur
                    user_data = {
                        "device_id": device_id,
                        "email": email,
                        "usage": {},
                        "premium": False,
                        "premium_until": None,
                        "created_at": datetime.now().isoformat()
                    }
                    self.db.collection('usage_tracking').document(device_id).set(user_data)
                    print(f"[UsageTracker] ✅ Supabase - New user created: {device_id}")
            except Exception as e:
                print(f"[UsageTracker] ❌ Supabase read hatası: {e}")
                # Fallback to memory
                user_data = self._memory_storage.get(device_id, {"usage": {}, "premium": False})
        else:
            # Memory/File storage
            data = self._load_data()
            if device_id not in data:
                data[device_id] = {"usage": {}, "premium": False, "premium_until": None}
                self._save_data(data)
            user_data = data[device_id]
        
        today_usage = user_data.get("usage", {}).get(today, 0)
        
        # Admin kontrolü - admin email'i varsa her zaman premium
        is_admin = self._is_admin(email)
        is_premium = is_admin or self._check_premium(user_data)
        
        remaining = "unlimited" if is_premium else max(0, self.FREE_DAILY_LIMIT - today_usage)
        
        result = {
            "device_id": device_id,
            "today_usage": today_usage,
            "daily_limit": self.FREE_DAILY_LIMIT,
            "remaining": remaining,
            "is_premium": is_premium,
            "is_admin": is_admin,
            "premium_until": "lifetime" if is_admin else user_data.get("premium_until"),
            "show_ads": not is_premium  # Admin ve premium kullanıcılara reklam gösterme
        }
        
        print(f"[UsageTracker] 📊 Result: {result}")
        
        return result
    
    def _is_admin(self, email: str) -> bool:
        """Email'in admin olup olmadığını kontrol et"""
        if not email:
            return False
        return email.strip().lower() in ADMIN_EMAILS
    
    def _check_premium(self, user_data: dict) -> bool:
        """Premium durumunu kontrol et"""
        if not user_data.get("premium"):
            return False
        premium_until = user_data.get("premium_until")
        if premium_until:
            return datetime.fromisoformat(premium_until) > datetime.now()
        return False
    
    def can_use_feature(self, device_id: str, feature: str = "ad_watch", email: str = None) -> dict:
        """
        Kullanıcı özelliği kullanabilir mi?
        feature: 'ad_watch' (analiz veya yorum için reklam izleme)
        """
        print(f"[UsageTracker] 🔍 can_use_feature - device_id: {device_id}, feature: {feature}, email: {email}")
        
        usage = self.get_user_usage(device_id, email)
        
        # Admin her zaman kullanabilir
        if usage.get("is_admin"):
            print(f"[UsageTracker] 👑 Admin user - unlimited access")
            return {"allowed": True, "reason": "admin", "remaining": "unlimited", "show_ads": False, "requires_ad": False}
        
        if usage["is_premium"]:
            print(f"[UsageTracker] 💎 Premium user - unlimited access")
            return {"allowed": True, "reason": "premium", "remaining": "unlimited", "show_ads": False, "requires_ad": False}
        
        # Ücretsiz kullanıcı - reklam izleme gerekli
        if usage["remaining"] > 0:
            print(f"[UsageTracker] ✅ Free user - {usage['remaining']} remaining, ad required")
            return {
                "allowed": True, 
                "reason": "free_quota", 
                "remaining": usage["remaining"], 
                "show_ads": True,
                "requires_ad": True,  # Reklam izleme ZORUNLU
                "message": f"Reklam izleyerek devam edebilirsiniz. Bugün {usage['remaining']} hakkınız kaldı."
            }
        
        print(f"[UsageTracker] ❌ Limit reached - premium required")
        return {
            "allowed": False, 
            "reason": "limit_reached",
            "message": "Günlük 3 ücretsiz hakkınız doldu. Premium'a geçin!",
            "remaining": 0,
            "show_ads": True,
            "requires_ad": False,
            "premium_price": self.PREMIUM_DAILY_PRICE
        }
    def record_usage(self, device_id: str, feature: str = "ad_watch", email: str = None) -> dict:
        """
        Kullanımı kaydet (reklam izleme)
        feature: 'ad_watch' - analiz veya yorum için reklam izlendi
        """
        today = date.today().isoformat()
        
        print(f"[UsageTracker] 📝 record_usage - device_id: {device_id}, feature: {feature}, email: {email}, today: {today}")
        
        # Supabase'e yaz
        if self.use_supabase:
            try:
                doc_ref = self.db.collection('usage_tracking').document(device_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    user_data = doc.to_dict()
                    print(f"[UsageTracker] ✅ Supabase - User found for recording")
                else:
                    user_data = {
                        "device_id": device_id,
                        "email": email,
                        "usage": {},
                        "premium": False,
                        "created_at": datetime.now().isoformat()
                    }
                    print(f"[UsageTracker] ✅ Supabase - New user created for recording")
                
                # Admin ve Premium kontrolü
                is_admin = self._is_admin(email)
                if not is_admin and not self._check_premium(user_data):
                    # Kullanımı artır
                    if "usage" not in user_data:
                        user_data["usage"] = {}
                    old_usage = user_data["usage"].get(today, 0)
                    user_data["usage"][today] = old_usage + 1
                    user_data["updated_at"] = datetime.now().isoformat()
                    doc_ref.set(user_data)
                    print(f"[UsageTracker] ✅ Supabase - Usage recorded: {old_usage} -> {old_usage + 1}")
                else:
                    print(f"[UsageTracker] ⚠️ Admin/Premium user - usage not recorded")
                
            except Exception as e:
                print(f"[UsageTracker] ❌ Supabase write hatası: {e}")
                # Fallback to memory
                if device_id not in self._memory_storage:
                    self._memory_storage[device_id] = {"usage": {}, "premium": False}
                if today not in self._memory_storage[device_id].get("usage", {}):
                    self._memory_storage[device_id]["usage"][today] = 0
                self._memory_storage[device_id]["usage"][today] += 1
        else:
            # Memory/File storage
            data = self._load_data()
            
            if device_id not in data:
                data[device_id] = {"usage": {}, "premium": False}
            
            if "usage" not in data[device_id]:
                data[device_id]["usage"] = {}
            
            if today not in data[device_id]["usage"]:
                data[device_id]["usage"][today] = 0
            
            # Admin ve Premium kullanıcı için limit yok, sayaç artmaz
            is_admin = self._is_admin(email)
            if not is_admin and not self._check_premium(data[device_id]):
                old_usage = data[device_id]["usage"][today]
                data[device_id]["usage"][today] += 1
                print(f"[UsageTracker] ✅ Memory - Usage recorded: {old_usage} -> {old_usage + 1}")
            
            self._save_data(data)
        
        result = self.get_user_usage(device_id, email)
        print(f"[UsageTracker] 📊 record_usage result: {result}")
        return result
    
    def set_premium(self, device_id: str, days: int = 30) -> dict:
        """Kullanıcıyı premium yap"""
        premium_until = datetime.now() + timedelta(days=days)
        
        # Supabase'e yaz
        if self.use_supabase:
            try:
                doc_ref = self.db.collection('usage_tracking').document(device_id)
                doc = doc_ref.get()
                
                if doc.exists:
                    user_data = doc.to_dict()
                else:
                    user_data = {
                        "device_id": device_id,
                        "usage": {},
                        "created_at": datetime.now().isoformat()
                    }
                
                user_data["premium"] = True
                user_data["premium_until"] = premium_until.isoformat()
                user_data["updated_at"] = datetime.now().isoformat()
                doc_ref.set(user_data)
                
            except Exception as e:
                print(f"[UsageTracker] Supabase premium set hatası: {e}")
                # Fallback to memory
                if device_id not in self._memory_storage:
                    self._memory_storage[device_id] = {"usage": {}}
                self._memory_storage[device_id]["premium"] = True
                self._memory_storage[device_id]["premium_until"] = premium_until.isoformat()
        else:
            # Memory/File storage
            data = self._load_data()
            
            if device_id not in data:
                data[device_id] = {"usage": {}, "premium": False}
            
            data[device_id]["premium"] = True
            data[device_id]["premium_until"] = premium_until.isoformat()
            
            self._save_data(data)
        
        return {"success": True, "premium_until": premium_until.isoformat()}
    
    def verify_purchase(self, device_id: str, purchase_token: str, product_id: str) -> dict:
        """Google Play satın alma doğrulama (placeholder)"""
        # TODO: Google Play Developer API ile doğrulama
        # Şimdilik basit bir implementasyon
        
        valid_products = {
            "premium_monthly": 30,
            "premium_yearly": 365,
            "premium_lifetime": 36500  # ~100 yıl
        }
        
        if product_id in valid_products:
            return self.set_premium(device_id, valid_products[product_id])
        
        return {"success": False, "error": "Invalid product"}
