"""
Kullanım Takip Sistemi
- Günlük ücretsiz AI yorum limiti (analiz değil, yorum!)
- Premium kullanıcı kontrolü
- Admin kullanıcı muafiyeti
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
    """Kullanıcı kullanım takibi - Günlük AI yorum limiti"""
    
    FREE_DAILY_LIMIT = 3  # Günlük ücretsiz AI YORUM sayısı (analiz değil!)
    
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
        
        # Supabase'den oku
        if self.use_supabase:
            try:
                doc = self.db.collection('usage_tracking').document(device_id).get()
                if doc.exists:
                    user_data = doc.to_dict()
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
            except Exception as e:
                print(f"[UsageTracker] Supabase read hatası: {e}")
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
        
        return {
            "device_id": device_id,
            "today_usage": today_usage,
            "daily_limit": self.FREE_DAILY_LIMIT,
            "remaining": "unlimited" if is_premium else max(0, self.FREE_DAILY_LIMIT - today_usage),
            "is_premium": is_premium,
            "is_admin": is_admin,
            "premium_until": "lifetime" if is_admin else user_data.get("premium_until"),
            "show_ads": not is_premium  # Admin ve premium kullanıcılara reklam gösterme
        }
    
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
    
    def can_use_feature(self, device_id: str, feature: str = "interpretation", email: str = None) -> dict:
        """Kullanıcı özelliği kullanabilir mi?"""
        usage = self.get_user_usage(device_id, email)
        
        # Admin her zaman kullanabilir
        if usage.get("is_admin"):
            return {"allowed": True, "reason": "admin", "remaining": "unlimited", "show_ads": False}
        
        if usage["is_premium"]:
            return {"allowed": True, "reason": "premium", "remaining": "unlimited", "show_ads": False}
        
        if usage["remaining"] > 0:
            return {"allowed": True, "reason": "free_quota", "remaining": usage["remaining"], "show_ads": True}
        
        return {
            "allowed": False, 
            "reason": "limit_reached",
            "message": "Günlük ücretsiz kullanım limitiniz doldu. Premium'a geçin!",
            "remaining": 0,
            "show_ads": True
        }
    def record_usage(self, device_id: str, feature: str = "interpretation", email: str = None) -> dict:
        """Kullanımı kaydet"""
        today = date.today().isoformat()
        
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
                        "email": email,
                        "usage": {},
                        "premium": False,
                        "created_at": datetime.now().isoformat()
                    }
                
                # Admin ve Premium kontrolü
                is_admin = self._is_admin(email)
                if not is_admin and not self._check_premium(user_data):
                    # Kullanımı artır
                    if "usage" not in user_data:
                        user_data["usage"] = {}
                    user_data["usage"][today] = user_data["usage"].get(today, 0) + 1
                    user_data["updated_at"] = datetime.now().isoformat()
                    doc_ref.set(user_data)
                
            except Exception as e:
                print(f"[UsageTracker] Supabase write hatası: {e}")
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
                data[device_id]["usage"][today] += 1
            
            self._save_data(data)
        
        return self.get_user_usage(device_id, email)
    
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
