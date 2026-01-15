"""
ORBIS Firebase Service
Push Notifications & Server-side Firestore işlemleri
"""

import os
import json
import firebase_admin
from firebase_admin import credentials, messaging, firestore
from typing import Optional, List, Dict, Any


class FirebaseService:
    """Firebase Admin SDK wrapper for ORBIS"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # db attribute'u her zaman tanımlı olsun
        if not hasattr(self, 'db'):
            self.db = None
        
        if not FirebaseService._initialized:
            self._init_firebase()
            FirebaseService._initialized = True
    
    def _init_firebase(self):
        """Firebase Admin SDK'yı başlat"""
        self.db = None  # Önce None olarak başlat
        
        try:
            # Credential dosyası yolu
            cred_path = os.environ.get('FIREBASE_CREDENTIALS_PATH')
            
            if cred_path and os.path.exists(cred_path):
                # Dosyadan yükle
                cred = credentials.Certificate(cred_path)
            elif os.environ.get('FIREBASE_CREDENTIALS_JSON'):
                # Environment variable'dan JSON olarak yükle
                cred_dict = json.loads(os.environ.get('FIREBASE_CREDENTIALS_JSON'))
                cred = credentials.Certificate(cred_dict)
            else:
                # Varsayılan konum
                default_paths = [
                    'orbis-ffa9e-firebase-adminsdk-fbsvc-b4ac1afabf.json',
                    'firebase-credentials.json',
                    'serviceAccountKey.json'
                ]
                
                cred = None
                for path in default_paths:
                    if os.path.exists(path):
                        cred = credentials.Certificate(path)
                        break
                
                if cred is None:
                    print("[Firebase] Credential dosyası bulunamadı!")
                    return
            
            # Firebase'i başlat (zaten başlatılmışsa atla)
            try:
                firebase_admin.get_app()
                print("[Firebase] Admin SDK zaten başlatılmış")
            except ValueError:
                firebase_admin.initialize_app(cred)
                print("[Firebase] Admin SDK başlatıldı")
            
            self.db = firestore.client()
            
        except Exception as e:
            print(f"[Firebase] Başlatma hatası: {e}")
            self.db = None
    
    # ═══════════════════════════════════════════════════════════════
    # PUSH NOTIFICATIONS
    # ═══════════════════════════════════════════════════════════════
    
    def send_push(
        self,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None
    ) -> Optional[str]:
        """
        Tek bir cihaza push notification gönder
        
        Args:
            token: FCM device token
            title: Bildirim başlığı
            body: Bildirim içeriği
            data: Ek veri (opsiyonel)
            image_url: Bildirim görseli (opsiyonel)
        
        Returns:
            Message ID veya None (hata durumunda)
        """
        try:
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )
            
            # Android özel ayarları - Ses sistem tarafından yönetilsin
            android_config = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='ic_notification',
                    color='#5b2bee',
                    # sound kaldırıldı - sistem varsayılan sesi kullanacak
                    channel_id='orbis_notifications',
                    click_action='FLUTTER_NOTIFICATION_CLICK'
                )
            )
            
            # iOS özel ayarları
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        badge=1,
                        sound='default'
                    )
                )
            )
            
            # Web push ayarları
            webpush_config = messaging.WebpushConfig(
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon='/static/all-icons/Android/Icon-192.png'
                )
            )
            
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=android_config,
                apns=apns_config,
                webpush=webpush_config
            )
            
            response = messaging.send(message)
            print(f"[Firebase] Push gönderildi: {response}")
            return response
            
        except messaging.UnregisteredError:
            print(f"[Firebase] Token geçersiz, siliniyor: {token[:20]}...")
            # Token'ı veritabanından sil
            self._remove_invalid_token(token)
            return None
            
        except Exception as e:
            print(f"[Firebase] Push hatası: {e}")
            return None
    
    def send_push_to_multiple(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Birden fazla cihaza push notification gönder
        
        Returns:
            {success_count, failure_count, responses}
        """
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens
            )
            
            response = messaging.send_each_for_multicast(message)
            
            # Başarısız token'ları temizle
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        if isinstance(resp.exception, messaging.UnregisteredError):
                            self._remove_invalid_token(tokens[idx])
            
            return {
                'success_count': response.success_count,
                'failure_count': response.failure_count,
                'responses': response.responses
            }
            
        except Exception as e:
            print(f"[Firebase] Multicast hatası: {e}")
            return {'success_count': 0, 'failure_count': len(tokens), 'error': str(e)}
    
    def send_push_to_topic(
        self,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Optional[str]:
        """
        Bir topic'e abone olan tüm cihazlara push gönder
        
        Topics:
            - 'all_users': Tüm kullanıcılar
            - 'premium_users': Premium kullanıcılar
            - 'daily_horoscope': Günlük burç yorumu isteyenler
        """
        try:
            # Android config - çift ses olmasın
            android_config = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    icon='ic_notification',
                    color='#5b2bee',
                    channel_id='orbis_notifications'
                )
            )
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                android=android_config,
                data=data or {},
                topic=topic
            )
            
            response = messaging.send(message)
            print(f"[Firebase] Topic push gönderildi ({topic}): {response}")
            return response
            
        except Exception as e:
            print(f"[Firebase] Topic push hatası: {e}")
            return None
    
    def subscribe_to_topic(self, tokens: List[str], topic: str) -> bool:
        """Cihazları bir topic'e abone et"""
        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            print(f"[Firebase] {response.success_count} cihaz '{topic}' topic'ine abone edildi")
            return response.success_count > 0
        except Exception as e:
            print(f"[Firebase] Topic subscribe hatası: {e}")
            return False
    
    def unsubscribe_from_topic(self, tokens: List[str], topic: str) -> bool:
        """Cihazları bir topic'ten çıkar"""
        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            return response.success_count > 0
        except Exception as e:
            print(f"[Firebase] Topic unsubscribe hatası: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # FIRESTORE OPERATIONS
    # ═══════════════════════════════════════════════════════════════
    
    def save_fcm_token(self, user_id: str, token: str, platform: str = 'web') -> bool:
        """Kullanıcının FCM token'ını kaydet"""
        if not self.db:
            return False
            
        try:
            from datetime import datetime
            
            self.db.collection('users').document(user_id).update({
                'fcmTokens': firestore.ArrayUnion([{
                    'token': token,
                    'platform': platform,
                    'updatedAt': datetime.utcnow().isoformat()
                }])
            })
            return True
        except Exception as e:
            print(f"[Firebase] Token kaydetme hatası: {e}")
            return False
    
    def get_user_tokens(self, user_id: str) -> List[str]:
        """Kullanıcının tüm FCM token'larını getir"""
        if not self.db:
            return []
            
        try:
            doc = self.db.collection('users').document(user_id).get()
            if doc.exists:
                data = doc.to_dict()
                tokens = data.get('fcmTokens', [])
                return [t['token'] for t in tokens if isinstance(t, dict)]
            return []
        except Exception as e:
            print(f"[Firebase] Token getirme hatası: {e}")
            return []
    
    def _remove_invalid_token(self, token: str):
        """Geçersiz token'ı tüm kullanıcılardan sil"""
        if not self.db:
            return
            
        try:
            # Token'ı içeren kullanıcıları bul ve sil
            users = self.db.collection('users').where(
                'fcmTokens', 'array_contains', {'token': token}
            ).stream()
            
            for user in users:
                self.db.collection('users').document(user.id).update({
                    'fcmTokens': firestore.ArrayRemove([{'token': token}])
                })
        except Exception as e:
            print(f"[Firebase] Token silme hatası: {e}")
    
    def activate_premium(
        self,
        user_id: str,
        package_id: str,
        credits: int,
        months: int
    ) -> bool:
        """
        Kullanıcıya premium aktivasyonu yap (satın alma sonrası)
        Bu fonksiyon sadece backend'den çağrılmalı!
        """
        if not self.db:
            return False
            
        try:
            from datetime import datetime, timedelta
            
            expiry_date = datetime.now() + timedelta(days=months * 30)
            
            self.db.collection('users').document(user_id).update({
                'isPremium': True,
                'premiumPackageId': package_id,
                'premiumExpiry': expiry_date.isoformat(),
                'credits': firestore.Increment(credits),
                'updatedAt': firestore.SERVER_TIMESTAMP
            })
            
            # Satın alma kaydı
            self.db.collection('purchases').add({
                'userId': user_id,
                'type': 'premium',
                'packageId': package_id,
                'credits': credits,
                'months': months,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            print(f"[Firebase] Premium aktivasyonu: {user_id} -> {package_id}")
            return True
            
        except Exception as e:
            print(f"[Firebase] Premium aktivasyon hatası: {e}")
            return False
    
    def add_credits(self, user_id: str, amount: int, package_price: float) -> bool:
        """Kullanıcıya kredi ekle (satın alma sonrası)"""
        if not self.db:
            return False
            
        try:
            self.db.collection('users').document(user_id).update({
                'credits': firestore.Increment(amount),
                'updatedAt': firestore.SERVER_TIMESTAMP
            })
            
            # Satın alma kaydı
            self.db.collection('purchases').add({
                'userId': user_id,
                'type': 'credits',
                'amount': amount,
                'price': package_price,
                'timestamp': firestore.SERVER_TIMESTAMP
            })
            
            return True
            
        except Exception as e:
            print(f"[Firebase] Kredi ekleme hatası: {e}")
            return False


# Singleton instance
firebase_service = FirebaseService()
