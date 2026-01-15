"""
Monetization API Routes
"""
from flask import Blueprint, request, jsonify
from monetization.usage_tracker import UsageTracker
from monetization.subscription import SubscriptionService

monetization_bp = Blueprint("monetization", __name__, url_prefix="/api/monetization")

usage_tracker = UsageTracker()
subscription_service = SubscriptionService()

@monetization_bp.route("/check-usage", methods=["POST"])
def check_usage():
    """Kullanıcının kullanım durumunu kontrol et"""
    data = request.get_json()
    device_id = data.get("device_id")
    email = data.get("email")  # Admin kontrolü için email
    
    if not device_id:
        return jsonify({"error": "device_id gerekli"}), 400
    
    usage = usage_tracker.get_user_usage(device_id, email)
    can_use = usage_tracker.can_use_feature(device_id, email=email)
    
    return jsonify({
        "usage": usage,
        "can_use": can_use,
        "show_ads": usage.get("show_ads", True)
    })

@monetization_bp.route("/record-usage", methods=["POST"])
def record_usage():
    """Kullanımı kaydet"""
    data = request.get_json()
    device_id = data.get("device_id")
    feature = data.get("feature", "interpretation")
    email = data.get("email")  # Admin kontrolü için email
    
    if not device_id:
        return jsonify({"error": "device_id gerekli"}), 400
    
    result = usage_tracker.record_usage(device_id, feature, email)
    return jsonify(result)

@monetization_bp.route("/plans", methods=["GET"])
def get_plans():
    """Abonelik planlarını getir"""
    return jsonify(subscription_service.get_plans())

@monetization_bp.route("/verify-purchase", methods=["POST"])
def verify_purchase():
    """Google Play satın alma doğrula"""
    data = request.get_json()
    device_id = data.get("device_id")
    purchase_token = data.get("purchase_token")
    product_id = data.get("product_id")
    
    if not all([device_id, purchase_token, product_id]):
        return jsonify({"error": "Eksik parametreler"}), 400
    
    result = usage_tracker.verify_purchase(device_id, purchase_token, product_id)
    return jsonify(result)

@monetization_bp.route("/premium-status", methods=["POST"])
def premium_status():
    """Premium durumunu kontrol et"""
    data = request.get_json()
    device_id = data.get("device_id")
    email = data.get("email")  # Admin kontrolü için email
    
    if not device_id:
        return jsonify({"error": "device_id gerekli"}), 400
    
    usage = usage_tracker.get_user_usage(device_id, email)
    return jsonify({
        "is_premium": usage["is_premium"],
        "is_admin": usage.get("is_admin", False),
        "premium_until": usage["premium_until"],
        "show_ads": usage.get("show_ads", True)
    })
