"""
ORBIS Admin Dashboard Routes
Premium kullanıcı yönetimi, kredi sistemi ve push bildirimleri
"""

from functools import wraps
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, session
from services.firebase_service import firebase_service
from exceptions import (
    ValidationError, DatabaseError, ConfigurationError,
    error_response, handle_errors
)
import os
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# ═══════════════════════════════════════════════════════════════
# ADMIN AUTHENTICATION
# ═══════════════════════════════════════════════════════════════

# Admin email listesi (environment variable'dan veya hardcoded)
ADMIN_EMAILS = os.environ.get('ADMIN_EMAILS', 'erkan@example.com').split(',')


def admin_required(f):
    """Admin yetkisi gerektiren route'lar için decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Session'dan admin kontrolü
        admin_email = session.get('admin_email')
        if not admin_email or admin_email not in ADMIN_EMAILS:
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/login', methods=['GET'])
def login():
    """Admin giriş sayfası"""
    return render_template('admin/login.html')


@admin_bp.route('/auth/verify', methods=['POST'])
@handle_errors("Admin doğrulama başarısız")
def verify_admin():
    """Firebase token'ı doğrula ve admin yetkisi kontrol et"""
    data = request.get_json()
    email = data.get('email')
    uid = data.get('uid')
    
    if not email:
        return jsonify({
            'success': False, 
            'error': 'EMAIL_REQUIRED',
            'message': 'Email gerekli'
        }), 400
    
    # Admin kontrolü
    if email not in ADMIN_EMAILS:
        logger.warning(f"Unauthorized admin access attempt: {email}")
        return jsonify({
            'success': False, 
            'error': 'FORBIDDEN',
            'message': 'Bu hesap admin yetkisine sahip değil'
        }), 403
    
    # Session'a kaydet
    session['admin_email'] = email
    session['admin_uid'] = uid
    
    logger.info(f"Admin login successful: {email}")
    
    return jsonify({
        'success': True,
        'redirect': url_for('admin.dashboard')
    })


@admin_bp.route('/logout')
def logout():
    """Admin çıkış"""
    session.pop('admin_email', None)
    session.pop('admin_uid', None)
    return redirect(url_for('admin.login'))


# ═══════════════════════════════════════════════════════════════
# DASHBOARD PAGES
# ═══════════════════════════════════════════════════════════════

@admin_bp.route('/')
@admin_required
def dashboard():
    """Ana dashboard sayfası"""
    return render_template('admin/dashboard.html')


@admin_bp.route('/users')
@admin_required
def users():
    """Kullanıcı listesi sayfası"""
    return render_template('admin/users.html')


@admin_bp.route('/users/<user_id>')
@admin_required
def user_detail(user_id):
    """Kullanıcı detay sayfası"""
    return render_template('admin/user_detail.html', user_id=user_id)


@admin_bp.route('/push')
@admin_required
def push_notifications():
    """Push bildirim gönderme sayfası"""
    return render_template('admin/push.html')


@admin_bp.route('/stats')
@admin_required
def statistics():
    """İstatistikler sayfası"""
    return render_template('admin/stats.html')


# ═══════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@admin_bp.route('/api/stats/overview', methods=['GET'])
@admin_required
@handle_errors("İstatistikler alınamadı")
def get_stats_overview():
    """Dashboard için genel istatistikler"""
    db = firebase_service.db
    if not db:
        return jsonify({
            'success': False,
            'error': 'DATABASE_UNAVAILABLE',
            'message': 'Firebase bağlantısı yok'
        }), 500
    
    # Kullanıcı sayıları
    users_ref = db.collection('users')
    all_users = list(users_ref.stream())
    
    total_users = len(all_users)
    premium_users = sum(1 for u in all_users if u.to_dict().get('isPremium', False))
    total_credits = sum(u.to_dict().get('credits', 0) for u in all_users)
    total_analyses = sum(u.to_dict().get('totalAnalyses', 0) for u in all_users)
    
    # Bugünkü aktif kullanıcılar
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    active_today = sum(
        1 for u in all_users 
        if u.to_dict().get('dailyUsage', {}).get('date') == today
    )
    
    return jsonify({
        'success': True,
        'data': {
            'totalUsers': total_users,
            'premiumUsers': premium_users,
            'freeUsers': total_users - premium_users,
            'totalCredits': total_credits,
            'totalAnalyses': total_analyses,
            'activeToday': active_today
        }
    })


@admin_bp.route('/api/users', methods=['GET'])
@admin_required
@handle_errors("Kullanıcı listesi alınamadı")
def get_users():
    """Kullanıcı listesi"""
    db = firebase_service.db
    if not db:
        return jsonify({
            'success': False,
            'error': 'DATABASE_UNAVAILABLE',
            'message': 'Firebase bağlantısı yok'
        }), 500
    
    # Query parametreleri
    limit = request.args.get('limit', 50, type=int)
    offset = request.args.get('offset', 0, type=int)
    filter_type = request.args.get('filter', 'all')  # all, premium, free
    search = request.args.get('search', '').lower()
    
    users_ref = db.collection('users')
    
    # Filter uygula
    if filter_type == 'premium':
        users_ref = users_ref.where('isPremium', '==', True)
    elif filter_type == 'free':
        users_ref = users_ref.where('isPremium', '==', False)
    
    # Tüm kullanıcıları al
    all_users = list(users_ref.stream())
    
    # Search filtresi
    if search:
        all_users = [
            u for u in all_users 
            if search in (u.to_dict().get('email', '') or '').lower()
            or search in (u.to_dict().get('displayName', '') or '').lower()
        ]
    
    # Pagination
    total = len(all_users)
    users = all_users[offset:offset + limit]
    
    # Format
    user_list = []
    for user in users:
        data = user.to_dict()
        user_list.append({
            'id': user.id,
            'email': data.get('email'),
            'displayName': data.get('displayName'),
            'photoURL': data.get('photoURL'),
            'isPremium': data.get('isPremium', False),
            'premiumPackageId': data.get('premiumPackageId'),
            'premiumExpiry': data.get('premiumExpiry'),
            'credits': data.get('credits', 0),
            'totalAnalyses': data.get('totalAnalyses', 0),
            'createdAt': data.get('createdAt'),
            'dailyUsage': data.get('dailyUsage', {})
        })
    
    return jsonify({
        'success': True,
        'data': {
            'users': user_list,
            'total': total,
            'limit': limit,
            'offset': offset
        }
    })


@admin_bp.route('/api/users/<user_id>', methods=['GET'])
@admin_required
@handle_errors("Kullanıcı detayı alınamadı")
def get_user_detail(user_id):
    """Tek kullanıcı detayı"""
    db = firebase_service.db
    if not db:
        return jsonify({
            'success': False,
            'error': 'DATABASE_UNAVAILABLE',
            'message': 'Firebase bağlantısı yok'
        }), 500
    
    doc = db.collection('users').document(user_id).get()
    
    if not doc.exists:
        return jsonify({
            'success': False, 
            'error': 'USER_NOT_FOUND',
            'message': 'Kullanıcı bulunamadı'
        }), 404
    
    data = doc.to_dict()
    
    # Satın alma geçmişi
    purchases = list(
        db.collection('purchases')
        .where('userId', '==', user_id)
        .order_by('timestamp', direction='DESCENDING')
        .limit(20)
        .stream()
    )
    
    purchase_list = []
    for p in purchases:
        pdata = p.to_dict()
        purchase_list.append({
            'id': p.id,
            'type': pdata.get('type'),
            'item': pdata.get('item') or pdata.get('packageId'),
            'amount': pdata.get('amount') or pdata.get('credits'),
            'timestamp': pdata.get('timestamp')
        })
    
    return jsonify({
        'success': True,
        'data': {
            'id': user_id,
            'email': data.get('email'),
            'displayName': data.get('displayName'),
            'photoURL': data.get('photoURL'),
            'isPremium': data.get('isPremium', False),
            'premiumPackageId': data.get('premiumPackageId'),
            'premiumExpiry': data.get('premiumExpiry'),
            'credits': data.get('credits', 0),
            'totalAnalyses': data.get('totalAnalyses', 0),
            'createdAt': data.get('createdAt'),
            'dailyUsage': data.get('dailyUsage', {}),
            'fcmTokens': data.get('fcmTokens', []),
            'purchases': purchase_list
        }
    })


@admin_bp.route('/api/users/<user_id>/premium', methods=['POST'])
@admin_required
@handle_errors("Premium durum güncellenemedi")
def update_user_premium(user_id):
    """Kullanıcı premium durumunu güncelle"""
    data = request.get_json()
    
    is_premium = data.get('isPremium', False)
    package_id = data.get('packageId')
    months = data.get('months', 1)
    credits = data.get('credits', 0)
    
    if is_premium:
        success = firebase_service.activate_premium(
            user_id, 
            package_id or 'admin_grant',
            credits,
            months
        )
    else:
        # Premium'u kaldır
        db = firebase_service.db
        db.collection('users').document(user_id).update({
            'isPremium': False,
            'premiumPackageId': None,
            'premiumExpiry': None
        })
        success = True
    
    return jsonify({
        'success': success,
        'message': 'Premium durumu güncellendi' if success else 'Güncelleme başarısız'
    })


@admin_bp.route('/api/users/<user_id>/credits', methods=['POST'])
@admin_required
@handle_errors("Kredi güncellenemedi")
def update_user_credits(user_id):
    """Kullanıcı kredisini güncelle"""
    data = request.get_json()
    
    action = data.get('action', 'add')  # add, set, subtract
    amount = data.get('amount', 0)
    
    db = firebase_service.db
    if not db:
        return jsonify({
            'success': False,
            'error': 'DATABASE_UNAVAILABLE',
            'message': 'Firebase bağlantısı yok'
        }), 500
    
    from firebase_admin import firestore
    
    if action == 'add':
        db.collection('users').document(user_id).update({
            'credits': firestore.Increment(amount)
        })
    elif action == 'subtract':
        db.collection('users').document(user_id).update({
            'credits': firestore.Increment(-amount)
        })
    elif action == 'set':
        db.collection('users').document(user_id).update({
            'credits': amount
        })
    
    # Admin log
    db.collection('admin_logs').add({
        'action': 'credit_update',
        'targetUser': user_id,
        'adminEmail': session.get('admin_email'),
        'details': {'action': action, 'amount': amount},
        'timestamp': firestore.SERVER_TIMESTAMP
    })
    
    logger.info(f"Credits updated for {user_id} by {session.get('admin_email')}: {action} {amount}")
    
    return jsonify({
        'success': True,
        'message': f'Kredi güncellendi ({action}: {amount})'
    })


@admin_bp.route('/api/push/send', methods=['POST'])
@admin_required
@handle_errors("Push bildirim gönderilemedi")
def send_push_notification():
    """Push bildirim gönder"""
    data = request.get_json()
    
    target_type = data.get('targetType')  # user, topic, all
    target = data.get('target')  # userId veya topic adı
    title = data.get('title')
    body = data.get('body')
    extra_data = data.get('data', {})
    
    if not all([target_type, title, body]):
        return jsonify({
            'success': False,
            'error': 'MISSING_PARAMS',
            'message': 'targetType, title ve body gerekli'
        }), 400
    
    result = None
    
    if target_type == 'user':
        tokens = firebase_service.get_user_tokens(target)
        if tokens:
            result = firebase_service.send_push_to_multiple(tokens, title, body, extra_data)
        else:
            return jsonify({
                'success': False,
                'error': 'NO_TOKENS',
                'message': 'Kullanıcının kayıtlı token\'ı yok'
            }), 404
            
    elif target_type == 'topic':
        result = firebase_service.send_push_to_topic(target, title, body, extra_data)
        
    elif target_type == 'all':
        result = firebase_service.send_push_to_topic('all_users', title, body, extra_data)
    
    # Admin log
    db = firebase_service.db
    if db:
        from firebase_admin import firestore
        db.collection('admin_logs').add({
            'action': 'push_sent',
            'adminEmail': session.get('admin_email'),
            'details': {
                'targetType': target_type,
                'target': target,
                'title': title
            },
            'timestamp': firestore.SERVER_TIMESTAMP
        })
    
    logger.info(f"Push notification sent by {session.get('admin_email')}: {target_type} - {title}")
    
    return jsonify({
        'success': result is not None,
        'result': result if isinstance(result, dict) else {'messageId': result}
    })


@admin_bp.route('/api/stats/purchases', methods=['GET'])
@admin_required
@handle_errors("Satın alma istatistikleri alınamadı")
def get_purchase_stats():
    """Satın alma istatistikleri"""
    db = firebase_service.db
    if not db:
        return jsonify({
            'success': False,
            'error': 'DATABASE_UNAVAILABLE',
            'message': 'Firebase bağlantısı yok'
        }), 500
    
    # Son 30 günlük satın almalar
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    purchases = list(
        db.collection('purchases')
        .where('timestamp', '>=', thirty_days_ago)
        .stream()
    )
    
    # Grupla
    premium_count = 0
    credit_count = 0
    total_credits_sold = 0
    
    for p in purchases:
        data = p.to_dict()
        if data.get('type') == 'premium':
            premium_count += 1
        elif data.get('type') == 'credits':
            credit_count += 1
            total_credits_sold += data.get('amount', 0)
    
    return jsonify({
        'success': True,
        'data': {
            'last30Days': {
                'premiumPurchases': premium_count,
                'creditPurchases': credit_count,
                'totalCreditsSold': total_credits_sold,
                'totalPurchases': len(purchases)
            }
        }
    })
