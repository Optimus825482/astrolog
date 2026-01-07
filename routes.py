from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    flash,
    redirect,
    url_for,
    current_app,
    Response,
    session,
    copy_current_request_context,
)

import ai_interpretations
from ai_interpretations_async import generate_interpretation_sync_wrapper
from astro_calculations import calculate_astro_data
from datetime import datetime, time
import json
import requests
import logging
from extensions import db
import astro_calculations
import uuid
import os
import threading
from concurrent.futures import ThreadPoolExecutor

# Utils modülünden helper fonksiyonlar
from utils import (
    parse_time_flexible,
    convert_times_to_str,
    get_element_class,
    Constants,
)

# Redis veya filesystem session storage seçimi
USE_REDIS_SESSION = os.getenv("SESSION_TYPE", "filesystem") == "redis"
IS_SERVERLESS = os.environ.get("VERCEL") or os.environ.get("NETLIFY") or os.environ.get("GAE_SERVICE")

if not USE_REDIS_SESSION:
    if IS_SERVERLESS:
        SESSION_DIR = "/tmp/sessions"
    else:
        SESSION_DIR = os.path.join(os.path.dirname(__file__), 'instance', 'sessions')
        
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR, exist_ok=True)

if IS_SERVERLESS:
    SETTINGS_FILE = "/tmp/settings.json"
else:
    SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'instance', 'settings.json')

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)

def save_session_data(data):
    """Session data'yı kaydet - Redis veya filesystem kullanır."""
    session_id = str(uuid.uuid4())
    
    if USE_REDIS_SESSION:
        # Redis kullan - Flask-Session otomatik serialize eder
        session[f'astro_data_{session_id}'] = data
    else:
        # Filesystem kullan
        filename = os.path.join(SESSION_DIR, f"astro_data_{session_id}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    return session_id

def load_session_data(session_id):
    """Session data'yı yükle - Redis veya filesystem kullanır."""
    if USE_REDIS_SESSION:
        # Redis'ten oku
        return session.get(f'astro_data_{session_id}')
    else:
        # Filesystem'den oku
        filename = os.path.join(SESSION_DIR, f"astro_data_{session_id}.json")
        if not os.path.exists(filename):
            return None
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
# Supabase import'unu güvenli hale getir
try:
    import supabase_service
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

bp = Blueprint("main", __name__)
logger = logging.getLogger(__name__)

@bp.route("/", endpoint="index")
def index():
    """Ana sayfaya yönlendirir"""
    return render_template("index.html")
@bp.route("/settings", methods=["GET", "POST"], endpoint="settings")
def settings():
    if request.method == "POST":
        settings_data = request.json
        save_settings(settings_data)
        flash("Ayarlar başarıyla kaydedildi!", "success")
        return jsonify({"status": "success"})
    
    current_settings = load_settings()
    return render_template("settings.html", settings=current_settings)


@bp.route("/about", endpoint="about")
def about():
    """Hakkında sayfası"""
    return render_template("about.html")


@bp.route("/dashboard", endpoint="dashboard")
def dashboard():
    # Kullanıcının doğum bilgilerini al (giriş yapmışsa)
    user_birth_data = None
    user_is_authenticated = False
    
    # Flask-Login'in mevcut olup olmadığını ve current_user'ın geçerli olup olmadığını kontrol et

    return render_template("dashboard.html", 
                         user_birth_data=user_birth_data,
                         user_is_authenticated=user_is_authenticated)


@bp.route("/my_calculations", endpoint="my_calculations")
def my_calculations():
    """Hesaplamaları gösterir"""
    return render_template("my_calculations.html", calculations=[])


@bp.route("/results", methods=["GET"])
def display_results():
    """Sonuç sayfasını gösterir."""
    try:
        session_id = request.args.get("session_id")
        if session_id:
            astro_data = load_session_data(session_id)
            if astro_data:
                return render_template("new_result.html", astro_data=astro_data)
            else:
                return render_template(
                    "new_result.html",
                    astro_data={},
                    use_local_storage=True,
                    default_error_message="Sonuç verisi bulunamadı. Lütfen tekrar hesaplama yapın.",
                )
        # Session_id yoksa eski davranış
        return render_template(
            "new_result.html",
            astro_data={},
            use_local_storage=True,
            default_error_message="Doğum haritası verileri bulunamadı. Lütfen Dashboard'a dönüp hesaplamaları tekrar yapın.",
        )
    except Exception as e:
        current_app.logger.error(
            f"Sonuç sayfası gösterme hatası: {str(e)}", exc_info=True
        )
        flash("Sonuçlar gösterilirken bir hata oluştu.")
        return redirect(url_for("main.dashboard"))


@bp.route("/show_results", methods=["POST"])
def show_results():
    try:
        # Formdan gelen verileri al
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        birth_date_str = data["birth_date"]
        birth_time_str = data["birth_time"]
        latitude_str = data["latitude"]
        longitude_str = data["longitude"]
        user_name = data.get("name", "Değerli Danışanım")
        analysis_type = data.get("analysis_type")
        transit_info = data.get("transit_info")

        # Tarih ve saat objelerini oluştur - utils fonksiyonları kullan
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        birth_time = parse_time_flexible(birth_time_str)
        
        latitude = float(latitude_str)
        longitude = float(longitude_str)
        # Astrolojik hesaplamaları yap
        astro_data = calculate_astro_data(
            birth_date=birth_date,
            birth_time=birth_time,
            latitude=latitude,
            longitude=longitude,
            transit_info=transit_info)
        if not astro_data or "error" in astro_data:
            current_app.logger.error(f"Astrolojik hesaplama hatası: {astro_data.get('error', 'Bilinmeyen hata')}")
            flash("Astrolojik hesaplama başarısız oldu. Lütfen doğum bilgilerinizi kontrol edin.")
            return redirect(url_for("main.dashboard"))

        # Kullanıcı adı ve doğum bilgilerini ekle
        astro_data["user_name"] = user_name
        astro_data["birth_info"] = {
            "date": birth_date_str,
            "time": birth_time_str,
            "datetime": f"{birth_date_str} {birth_time_str}",
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "name": data.get("birth_place", ""),
            },
        }

        # --- ANAHTAR ORGANİZASYONU ---
        expected_keys = [
            # NATAL
            "natal_houses", "natal_planet_positions", "natal_additional_points", "natal_aspects", "natal_fixed_stars", "natal_arabic_parts", "natal_antiscia", "natal_dignity_scores", "natal_midpoint_analysis", "natal_lunation_cycle", "natal_declinations", "natal_part_of_fortune", "natal_summary_interpretation", "eclipses_nearby_birth",
            # TRANSIT
            "transit_positions", "transit_houses", "transit_aspects", "transit_to_natal_aspects", "transit_azimuth_altitude", "eclipses_nearby_current",
            # PROGRESYON
            "progressed_positions", "progressed_aspects", "progressed_to_natal_aspects",
            # DİĞER
            "sun_sign", "moon_sign", "ascendant_sign", "midheaven_sign", "chart_ruler", "element_balance", "quality_balance", "lunar_phase", "planetary_strengths"
        ]

        # Eksik anahtarları None ile doldur
        for key in expected_keys:
            if key not in astro_data:
                astro_data[key] = None

        # Session'ı kaydet
        session_id = save_session_data(astro_data)

        return render_template("new_result.html", astro_data=astro_data)

    except Exception as e:
        current_app.logger.error(f"show_results hatası: {str(e)}", exc_info=True)
        flash("Sonuçlar işlenirken bir hata oluştu.")
        return redirect(url_for("main.dashboard"))


@bp.route("/api/get_ai_interpretation", methods=["POST"])
def api_get_ai_interpretation():
    try:
        data = request.get_json()
        interpretation_type = data.get("interpretation_type", "daily")
        astro_data = data.get("astro_data", {})
        user_name = data.get("user_name", "Değerli Danışanım")
        
        # ai_interpretations.py içindeki ana yorum motorunu çağır (Zai/GLM-4.7 öncelikli)
        result = ai_interpretations.get_ai_interpretation_engine(astro_data, interpretation_type, user_name)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"api_get_ai_interpretation hatası: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/generate_interpretation", methods=["POST"])
def generate_interpretation():
    try:
        data = request.get_json()
        provider = data.get("provider", "natal")
        chart_data = data.get("chartData", {})
        custom_prompt = data.get("customPrompt", "")

        # AI yorumunu oluştur - Async wrapper kullan (non-blocking)
        result = generate_interpretation_sync_wrapper(
            provider=provider,
            chart_data=chart_data,
            custom_prompt=custom_prompt
        )
        
        if not result:
            return jsonify({"success": False, "error": "Yorum oluşturulamadı"}), 500
        
        if result.get("success"):
            interpretation = result.get("interpretation", "")
            return jsonify({"success": True, "interpretation": interpretation})
        else:
            error_msg = result.get("error", "Bilinmeyen hata")
            return jsonify({"success": False, "error": error_msg}), 500

    except Exception as e:
        current_app.logger.error(f"generate_interpretation hatası: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/location_search", methods=["POST"])
def location_search():
    try:
        data = request.get_json()
        query = data.get("query", "")

        if not query:
            return jsonify({"error": "Query parameter required"}), 400

        # OpenCage API ile konum araması
        from config import Config
        api_key = getattr(Config, 'OPENCAGE_API_KEY', None)
        
        if not api_key:
            return jsonify({"error": "OpenCage API key not configured"}), 500

        url = "https://api.opencagedata.com/geocode/v1/json"
        params = {
            "q": query,
            "key": api_key,
            "limit": 5,
            "language": "tr"
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()

        results = response.json().get("results", [])

        locations = []
        for result in results:
            location = {
                "name": result.get("formatted"),
                "latitude": result["geometry"]["lat"],
                "longitude": result["geometry"]["lng"],
                "country": result.get("components", {}).get("country", ""),
                "city": result.get("components", {}).get("city", "") or result.get("components", {}).get("town", "") or result.get("components", {}).get("village", "")
            }
            locations.append(location)

        return jsonify({"success": True, "locations": locations})

    except requests.RequestException as e:
        current_app.logger.error(f"location_search API hatası: {str(e)}")
        return jsonify({"error": "Konum araması başarısız oldu"}), 500
    except Exception as e:
        current_app.logger.error(f"location_search hatası: {str(e)}", exc_info=True)
        return jsonify({"error": "Beklenmeyen bir hata oluştu"}), 500


@bp.route("/api/save_calculation", methods=["POST"])
def save_calculation():
    try:
        data = request.get_json()
        
        if not SUPABASE_AVAILABLE:
            return jsonify({"success": False, "error": "Veritabanı servisi mevcut değil"}), 500

        # Supabase'e kaydet
        result = supabase_service.save_calculation(data)
        
        if result and "error" not in result:
            return jsonify({"success": True, "id": result.get("id")})
        else:
            error_msg = result.get("error", "Bilinmeyen hata") if result else "Kayıt başarısız"
            return jsonify({"success": False, "error": error_msg}), 500

    except Exception as e:
        current_app.logger.error(f"save_calculation hatası: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/load_calculation/<calculation_id>", methods=["GET"])
def load_calculation(calculation_id):
    try:
        if not SUPABASE_AVAILABLE:
            return jsonify({"success": False, "error": "Veritabanı servisi mevcut değil"}), 500

        # Supabase'den yükle
        result = supabase_service.load_calculation(calculation_id)
        
        if result and "error" not in result:
            return jsonify({"success": True, "data": result})
        else:
            error_msg = result.get("error", "Bilinmeyen hata") if result else "Yükleme başarısız"
            return jsonify({"success": False, "error": error_msg}), 500

    except Exception as e:
        current_app.logger.error(f"load_calculation hatası: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/api/tts", methods=["POST"])
def text_to_speech():
    try:
        data = request.get_json()
        text = data.get("text", "")

        if not text:
            return jsonify({"error": "Text parameter required"}), 400

        # Background task olarak çalıştır - non-blocking
        def generate_tts_background():
            try:
                from config import Config
                api_key = getattr(Config, 'GOOGLE_API_KEY', None)
                
                if not api_key:
                    current_app.logger.error("Google Cloud API key not configured")
                    return {"success": False, "error": "API key not configured"}
                
                url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
                payload = {
                    "input": {"text": text},
                    "voice": {"languageCode": "tr-TR", "name": "tr-TR-Wavenet-A"},
                    "audioConfig": {"audioEncoding": "MP3"}
                }
                
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                
                audio_content = response.json().get("audioContent", "")
                return {"success": True, "audio": audio_content}
                
            except requests.RequestException as e:
                current_app.logger.error(f"TTS API hatası: {str(e)}")
                return {"success": False, "error": str(e)}
            except Exception as e:
                current_app.logger.error(f"TTS generation error: {str(e)}")
                return {"success": False, "error": str(e)}
        
        # Thread pool ile background task çalıştır
        executor = ThreadPoolExecutor(max_workers=2)
        future = executor.submit(generate_tts_background)
        result = future.result(timeout=15)  # 15 saniye timeout
        executor.shutdown(wait=False)
        
        if result.get("success"):
            return jsonify(result)
        else:
            return jsonify({"error": result.get("error", "Beklenmeyen hata")}), 500
        
    except Exception as e:
        current_app.logger.error(f"text_to_speech hatası: {str(e)}", exc_info=True)
        return jsonify({"error": "Beklenmeyen bir hata oluştu"}), 500
        # Google TTS API kullanımı
        from config import Config
        api_key = getattr(Config, 'GOOGLE_API_KEY', None)
        
        if not api_key:
            return jsonify({"error": "Google Cloud API key not configured"}), 500

        # TTS isteği (background task olarak çalıştırılabilir)
        # Şimdilik basit implementation
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
        payload = {
            "input": {"text": text},
            "voice": {"languageCode": "tr-TR", "name": "tr-TR-Wavenet-A"},
            "audioConfig": {"audioEncoding": "MP3"}
        }

        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()

        audio_content = response.json().get("audioContent", "")

        return jsonify({"success": True, "audio": audio_content})

    except requests.RequestException as e:
        current_app.logger.error(f"TTS API hatası: {str(e)}")
        return jsonify({"error": "Ses sentezi başarısız oldu"}), 500
    except Exception as e:
        current_app.logger.error(f"text_to_speech hatası: {str(e)}", exc_info=True)
        return jsonify({"error": "Beklenmeyen bir hata oluştu"}), 500
