from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    jsonify,
    session,
    flash,
    current_app,
    g,
)
from flask_session import Session  # Flask-Session modülünü içe aktar
from astro_calculations import calculate_astro_data
import os
from datetime import datetime, date, time
import json
from flask.json.provider import DefaultJSONProvider
import requests
from requests.adapters import HTTPAdapter
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import logging

# from .tts_server import create_tts_app # Replaced by tts_utils
from datetime import timedelta
from location_service import LocationService

from dotenv import load_dotenv

# from ai_interpretations import get_hyperbolic_interpretation # Eski importu yorum satırı yap veya sil
from ai_interpretations import (
    get_ai_interpretation_engine,
)  # Merkezi yorum motorunu import et

# Load environment variables (optional, but good practice if .env is used)
load_dotenv()

# Logging yapılandırması
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Flask uygulaması
app = Flask(__name__, static_folder="static", static_url_path="/static")

# Configuration import from config.py
from config import Config

# Apply configuration
app.config.from_object(Config)

# Session configuration - Environment-aware setup
app.config["SESSION_FILE_DIR"] = os.path.join(app.instance_path, "sessions")
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_FILE_THRESHOLD"] = 100  # Maksimum session dosyası sayısını azalt
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_NAME"] = "astro_session"
app.config["SESSION_FILE_MODE"] = 0o600  # Session dosyası erişim izinlerini sınırla

# SESSION_COOKIE_SECURE environment'dan gelir (config.py'de ayarlı)

# Create session directory if it doesn't exist
os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)

# HYPERBOLIC_API_KEY - Artık environment'dan okunuyor (Task 1)
# Bu satır backward compatibility için tutuldu
HYPERBOLIC_API_KEY = os.getenv(
    "HYPERBOLIC_API_KEY",
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJpa2luY2l5ZW5pa2l0YXA1NEBnbWFpbC5jb20iLCJpYXQiOjE3MjY5MzkwNjl9.fIXOKvamoJLKvAhpnhl7pelXSwzmXMcNF8ZVR2uQGrY",
)


# =============================================================================
# RESOURCE MANAGEMENT - Memory leak prevention and cleanup
# =============================================================================
from resource_cleanup import init_resource_management
init_resource_management(app)


# =============================================================================
# CACHE CONFIGURATION - Flask-Caching with Redis backend
# =============================================================================
from cache_config import init_cache
init_cache(app)


# =============================================================================
# CONTEXT-AWARE HTTP SESSION - Flask g object ile per-request lifecycle
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.strftime("%H:%M")
        return super().default(obj)


# JSON serileştirme için özel provider (Flask 2.2+ için modern yöntem)
class DateTimeJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, time):
            return obj.strftime("%H:%M")
        return super().default(obj)


# JSON provider'ı kaydet
app.json = DateTimeJSONProvider(app)



# =============================================================================
# CONTEXT-AWARE HTTP SESSION - Flask g object ile per-request lifecycle
# =============================================================================
@app.before_request
def create_http_session():
    """Her request için yeni bir HTTP session oluştur (context-aware)."""
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    
    # Retry strategy - daha sağlam bağlantı için
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    # Session oluştur ve connection pooling ayarla
    http_session = requests.Session()
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,  # Connection pool size
        pool_maxsize=10,
    )
    http_session.mount("http://", adapter)
    http_session.mount("https://", adapter)
    
    # Flask g object ile per-request storage
    g.http_session = http_session


@app.teardown_request
def cleanup_http_session(exception=None):
    """Request sonunda HTTP session'ı temizle."""
    if hasattr(g, 'http_session'):
        g.http_session.close()


# Gezegen sembolü filtresi
def get_planet_symbol(planet_name):
    """Jinja2 filtresi: Gezegen adından sembol döndürür."""
    symbols = {
        "Sun": "☉",
        "Moon": "☽",
        "Mercury": "☿",
        "Venus": "♀",
        "Mars": "♂",
        "Jupiter": "♃",
        "Saturn": "♄",
        "Uranus": "♅",
        "Neptune": "♆",
        "Pluto": "♇",
    }
    return symbols.get(planet_name, planet_name)


# Element sınıfı filtresi
def element_class(sign):
    """Jinja2 filtresi: Burç isminden CSS sınıfı döndürür."""
    element_classes = {
        "Koç": "fire",
        "Aslan": "fire",
        "Yay": "fire",
        "Boğa": "earth",
        "Başak": "earth",
        "Oğlak": "earth",
        "İkizler": "air",
        "Terazi": "air",
        "Kova": "air",
        "Yengeç": "water",
        "Akrep": "water",
        "Balık": "water",
    }
    return element_classes.get(sign, "")


# Zodyak burcu filtresi
def get_zodiac_sign(degree):
    """Jinja2 filtresi: Dereceye göre Zodyak burcunu döndürür."""
    signs = [
        (0, "Koç"), (30, "Boğa"), (60, "İkizler"), (90, "Yengeç"),
        (120, "Aslan"), (150, "Başak"), (180, "Terazi"), (210, "Akrep"),
        (240, "Yay"), (270, "Oğlak"), (300, "Kova"), (330, "Balık")
    ]
    degree = float(degree) % 360  # Dereceyi 0-360 aralığına normalize et
    for sign_degree, sign_name in reversed(signs):
        if degree >= sign_degree:
            return sign_name
    return "Bilinmeyen" # Bu durum normalde oluşmamalı


@app.template_filter("safe_round")
def safe_round(value, decimals=2):
    """Güvenli yuvarlama filtresi."""
    try:
        if value is None:
            return "-"
        val = float(value)
        return round(val, decimals) if not isinstance(val, str) else "-"
    except (ValueError, TypeError):
        return "-"


# Jinja2 filtrelerini kaydet
app.jinja_env.filters["planet_symbol"] = get_planet_symbol 
app.jinja_env.filters["element_class"] = element_class
app.jinja_env.filters["get_zodiac_sign"] = get_zodiac_sign
app.jinja_env.filters["safe_round"] = safe_round


# Ana sayfa
@app.route("/")
def index():
    return render_template(
        "index.html", opencage_api_key=app.config["OPENCAGE_API_KEY"]
    )


# Dashboard
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    return render_template("dashboard.html")


# Hesaplama rotası
@app.route("/perform_calculation", methods=["POST"])
def perform_calculation():
    """Astrolojik hesaplamaları yapar ve sonuçları kaydeder."""
    try:
        if not request.form:
            flash("Form verisi bulunamadı.", "error")
            return redirect(url_for("dashboard"))

        session["calculation_complete"] = True

        data = request.form

        # Form verilerini alırken None kontrolü yap veya varsayılan değer ata
        birth_date_str = data.get("birth_date")
        birth_time_str = data.get("birth_time")
        latitude_str = data.get("latitude")
        longitude_str = data.get("longitude")

        birth_date = None
        if birth_date_str:
            try:
                birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Geçersiz doğum tarihi formatı.", "error")
                return redirect(url_for("dashboard"))

        birth_time = None
        if birth_time_str:
            try:
                birth_time = datetime.strptime(birth_time_str, "%H:%M").time()
            except ValueError:
                flash("Geçersiz doğum saati formatı.", "error")
                return redirect(url_for("dashboard"))

        latitude = None
        if latitude_str:
            try:
                latitude = float(latitude_str)
            except ValueError:
                flash("Geçersiz enlem formatı.", "error")
                return redirect(url_for("dashboard"))

        longitude = None
        if longitude_str:
            try:
                longitude = float(longitude_str)
            except ValueError:
                flash("Geçersiz boylam formatı.", "error")
                return redirect(url_for("dashboard"))

        # Gerekli alanların dolu olduğunu kontrol et
        if not birth_date or not birth_time or latitude is None or longitude is None:
             flash("Doğum tarihi, saati, enlem ve boylam bilgileri eksik veya hatalı.", "error")
             return redirect(url_for("dashboard"))

        # BirthInfo modelinin import edildiği varsayılarak kullanılıyor
        # birth_info = BirthInfo(
        #     name=data.get("name"),
        #     birth_date=birth_date,
        #     birth_time=birth_time,
        #     birth_place=data.get("birth_place"),
        #     latitude=latitude,
        #     longitude=longitude,
        # )

        # Calculate astro data
        # calculate_astro_data fonksiyonunun datetime objesi beklediği varsayılıyor
        birth_dt_obj = datetime.combine(birth_date, birth_time)
        astro_data = calculate_astro_data(
            birth_date=birth_dt_obj, # datetime objesini gönder
            birth_time=birth_dt_obj.time(), # time objesini gönder (calculate_astro_data'nın beklediği formata göre ayarlanmalı)
            latitude=latitude,
            longitude=longitude,
        )

        # Add name to astro_data
        astro_data["name"] = data.get("name", "Anonymous")

        # Save to session file with proper JSON encoding
        session_dir = os.path.join(app.instance_path, "sessions")
        os.makedirs(session_dir, exist_ok=True)
        # birth_info.id yerine zaman damgası veya başka bir benzersiz tanımlayıcı kullan
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        session_file = os.path.join(session_dir, f"astro_data_{timestamp}.json")

        # Veriyi JSON formatına dönüştürmeden önce houses verilerini düzelt
        result_data = astro_data.copy()
        if "houses" in result_data:
            if "Houses" in result_data["houses"]:
                result_data["houses"]["Houses"] = {
                    str(k): float(v) for k, v in result_data["houses"]["Houses"].items()
                }
            if "house_cusps" in result_data["houses"]:
                result_data["houses"]["house_cusps"] = {
                    str(k): float(v)
                    for k, v in result_data["houses"]["house_cusps"].items()
                }

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(result_data, f, cls=DateTimeEncoder, ensure_ascii=False, indent=2)

        # Analysis ve BirthInfo modellerinin import edildiği varsayılarak kullanılıyor
        # try:
        #     # BirthInfo kaydını bul veya oluştur
        #     birth_info = BirthInfo.query.filter_by(
        #         name=data.get("name"),
        #         birth_date=birth_date,
        #         birth_time=birth_time,
        #         latitude=latitude,
        #         longitude=longitude
        #     ).first()
        #
        #     if not birth_info:
        #         birth_info = BirthInfo(
        #             name=data.get("name"),
        #             birth_date=birth_date,
        #             birth_time=birth_time,
        #             birth_place=data.get("birth_place"),
        #             latitude=latitude,
        #             longitude=longitude,
        #         )
        #         db.session.add(birth_info)
        #         db.session.commit()
        #
        #     # Analysis kaydını oluştur
        #     analysis = Analysis(
        #         birth_info_id=birth_info.id,
        #         analysis_type="natal",
        #         result=result_data,
        #         name=data.get("name"),
        #     )
        #     db.session.add(analysis)
        #     db.session.commit()
        #
        #     session["birth_info_id"] = birth_info.id
        #     session["name"] = data.get("name")
        #     session["calculation_complete"] = True
        #
        # except Exception as db_error:
        #     logging.error(f"Veritabanı kaydetme hatası: {str(db_error)}")
        #     flash(f"Sonuçlar kaydedilirken bir hata oluştu: {str(db_error)}", "error")
        #     # Veritabanı hatası olsa bile hesaplanan veriyi session'a kaydetmeye devam et
        #     session["astro_data"] = result_data # Hesaplanan veriyi session'a kaydet
        #     session["birth_info"] = { # birth_info'yu da session'a kaydet
        #         "name": data.get("name"),
        #         "birth_date": birth_date,
        #         "birth_time": birth_time,
        #         "birth_place": data.get("birth_place"),
        #         "latitude": latitude,
        #         "longitude": longitude,
        #     }
        #     session["calculation_complete"] = True
        #     # Hata durumunda bile sonuç sayfasına yönlendir
        #     return redirect(url_for("main.results"))


        # Veritabanı işlemleri şimdilik yorum satırı yapıldı, sadece session'a kaydet
        session["astro_data"] = astro_data # Hesaplanan veriyi session'a kaydet
        session["birth_info"] = { # birth_info'yu da session'a kaydet
            "name": data.get("name"),
            "birth_date": birth_date,
            "birth_time": birth_time,
            "birth_place": data.get("birth_place"),
            "latitude": latitude,
            "longitude": longitude,
        }
        session["calculation_complete"] = True
        # session["birth_info_id"] = None # Veritabanı kullanılmadığı için id yok
        # session["name"] = data.get("name") # Zaten birth_info içinde var

        # Başarılı hesaplama sonrası sonuç sayfasına yönlendir
        return redirect(url_for("main.results"))

    except Exception as e:
        logging.error(f"Calculate hatası: {str(e)}")

        flash(f"Hesaplama hatası: {str(e)}", "error")
        return redirect(url_for("dashboard"))


# get_birth_records endpoint routes.py dosyasına taşındı


# Sonuçlar rotası

import collections.abc

def convert_times_to_str(obj):
    """Tüm dict/list içindeki datetime.time ve datetime.date objelerini stringe çevirir."""
    import datetime
    if isinstance(obj, dict):
        return {k: convert_times_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_times_to_str(i) for i in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_times_to_str(i) for i in obj)
    elif isinstance(obj, datetime.time):
        return obj.strftime("%H:%M")
    elif isinstance(obj, datetime.date):
        return obj.strftime("%Y-%m-%d")
    else:
        return obj


# @app.route("/results", methods=["GET"]) - routes.py içinde blueprint'e bağlı olarak daha gelişmiş bir rota var
# def results():
#     """Sonuçları görüntüler."""
#     # Sonuçları session'dan al
#     astro_data = session.get("astro_data")
#     birth_info = session.get("birth_info")
#     # name = session.get("name") # birth_info içinde var
#
#     if not astro_data or not birth_info:
#         flash("Sonuçlar bulunamadı, lütfen tekrar hesaplama yapın.", "warning")
#         return redirect(url_for("main.dashboard")) # main blueprint'ini belirt
#
#     # Yorumları session'dan al (eğer kaydedildiyse)
#     # Veritabanı işlemleri yorum satırı yapıldığı için yorumlar şimdilik session'dan alınmıyor
#     # interpretations = session.get("interpretation_data", [])
#     interpretation_data = [] # Şimdilik boş liste
#
#     # Tüm time ve date objelerini stringe çevir
#     astro_data_str = convert_times_to_str(astro_data)
#     birth_info_str = convert_times_to_str(birth_info)
#
#     return render_template(
#         "new_result.html",
#         astro_data=astro_data_str,
#         birth_info=birth_info_str,
#         name=birth_info.get("name"), # birth_info dict'inden adı al
#         interpretation_data=interpretation_data,
#     )


# @app.route("/get_ai_interpretation", methods=["POST"]) - routes.py içinde blueprint'e bağlı olarak daha gelişmiş bir rota var
# def get_ai_interpretation():
#     """Hyperbolic API ile astrolojik yorum alır."""
#     try:
#         data = request.get_json()
#         if not data or "type" not in data:
#             return jsonify({"error": "Geçersiz veri formatı!"}), 400
#
#         # Hyperbolic API isteği
#         headers = {
#             "Authorization": f"Bearer {HYPERBOLIC_API_KEY}",
#             "Content-Type": "application/json",
#         }
#
#         payload = {
#             "model": "deepseek-ai/DeepSeek-V3-0324",
#             "messages": [{"role": "user", "content": str(data.get("astro_data", {}))}],
#             "max_tokens": 40282,
#             "temperature": 0.87,
#             "top_p": 0.9,
#         }
#
#         response = requests.post(
#             "https://api.hyperbolic.xyz/v1/chat/completions",
#             headers=headers,
#             json=payload,
#         )
#         response.raise_for_status()
#
#         return jsonify(response.json()), 200
#     except requests.RequestException as e:
#         logging.error(f"Hyperbolic API hatası: {str(e)}")
#         return jsonify({"error": str(e)}), 500
#     except Exception as e:
#         logging.error(f"Yorum alma hatası: {str(e)}")
#         return jsonify({"error": str(e)}), 500


@app.route("/api/search-location", methods=["GET"])
def search_location():
    """Verilen konum bilgisine göre enlem ve boylam döndürür."""
    global location_service
    try:
        query = request.args.get("query", "")
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400

        # Location service kontrolü
        if not _services_initialized:
            initialize_services()
        if not location_service:
            return jsonify({"error": "Location service unavailable"}), 503

        # Önce location service ile dene
        try:
            results = location_service.search_location(query)
            if results:
                return jsonify(results)
        except Exception as e:
            logger.warning(
                f"Location service failed, falling back to OpenCage: {str(e)}"
            )

        # OpenCage fallback
        opencage_key = app.config.get("OPENCAGE_API_KEY")
        if not opencage_key:
            return jsonify({"error": "Geocoding service unavailable"}), 503

        url = f"https://api.opencagedata.com/geocode/v1/json"
        params = {"q": query, "key": opencage_key, "language": "tr", "limit": 5}

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            results = []
            for result in data["results"]:
                formatted_result = {
                    "display_name": result["formatted"],
                    "latitude": result["geometry"]["lat"],
                    "longitude": result["geometry"]["lng"],
                    "type": "city",
                    "importance": result.get("importance", 0),
                    "components": {
                        "city": result["components"].get("city")
                        or result["components"].get("town")
                        or result["components"].get("village"),
                        "state": result["components"].get("state"),
                        "country": result["components"].get("country"),
                    },
                }
                results.append(formatted_result)
            return jsonify(results)

        return jsonify({"error": "Location not found"}), 404

    except requests.RequestException as e:
        logger.error(f"OpenCage API request error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Location search error: {str(e)}")
        return jsonify({"error": str(e)}), 500


# initialize_services fonksiyonunun @app.before_request ile tanımlanmış hali kullanılıyor
# def initialize_services():
#     """Location service'ı başlatır."""
#     global location_service
#     location_service = LocationService()


@app.route("/astro_analysis", methods=["POST"])
def astro_analysis():
    """Astrolojik analiz endpoint'i."""
    try:
        data = request.get_json()
        name = data.get("name")
        birth_date = data.get("birth_date")
        birth_time = data.get("birth_time")
        latitude = float(data.get("latitude"))
        longitude = float(data.get("longitude"))

        # Doğrulama
        birth_dt = datetime.strptime(birth_date, "%Y-%m-%d")
        if birth_dt > datetime.now():
            return jsonify({"error": "Doğum tarihi gelecekte olamaz!"}), 400
        datetime.strptime(birth_time, "%H:%M")
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return jsonify({"error": "Geçersiz koordinatlar!"}), 400

        result = calculate_astro_data(birth_date, birth_time, latitude, longitude, name)
        return jsonify(result)

    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Giriş hatası: {str(e)}"}), 400
    except Exception as e:
        logging.error(f"Astro analiz hatası: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/get_ai_interpretation2", methods=["POST"])
def inter():
    return render_template("404.html")


# @app.route("/api/get_ai_interpretation", methods=["POST"])
# def api_get_ai_interpretation():
#     """Frontend'den gelen istekle AI yorumu alır."""
#     print("API isteği alındı.")
#     try:
#         data = request.get_json()
#         if not data or "type" not in data or "astro_data" not in data:
#             return jsonify(
#                 {"success": False, "error": "Eksik veya geçersiz veri."}
#             ), 400
# 
#         interpretation_type = data.get("type")
#         astro_data = data.get("astro_data")
#         user_name = data.get(
#             "user_name", session.get("name", "Değerli Danışanım")
#         )  # Kullanıcı adını al
# 
#         # Merkezi yorum motorunu çağır
#         ai_result = get_ai_interpretation_engine(
#             astro_data=astro_data,
#             interpretation_type=interpretation_type,
#             user_name=user_name,
#         )
# 
#         return jsonify(ai_result)
# 
#     except Exception as e:
#         logging.error(f"AI Yorum API hatası: {str(e)}", exc_info=True)
#         return jsonify({"success": False, "error": f"Sunucu hatası: {str(e)}"}), 500


@app.route("/api/tts", methods=["POST"])
def api_tts():
    """Metni sese çevirir ve ses dosyasını döndürür."""
    try:
        data = request.get_json()
        text = data.get("text")
        action = data.get("action", "play")  # 'play', 'pause', 'stop' gibi aksiyonlar
        rate = data.get("rate", "+0%")  # Hız ayarı

        if not text:
            return jsonify({"error": "Metin sağlanmadı."}), 400

        # TTS motorunu burada çağır (örnek: gTTS veya pyttsx3)
        # Şimdilik örnek olarak bir ses dosyası oluşturulmuş gibi davranalım
        from gtts import gTTS
        import io
        from flask import send_file

        tts = gTTS(text, lang="tr")
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return send_file(mp3_fp, mimetype="audio/mpeg")

    except Exception as e:
        logging.error(f"TTS API hatası: {str(e)}", exc_info=True)
        return jsonify({"error": f"Sunucu hatası: {str(e)}"}), 500


# Global HTTP session oluştur - adını değiştir
http_session = requests.Session()
# retries = Retry(total=3, backoff_factor=1) # Retry kullanımı yorum satırı yapıldı
http_session.mount("https://", HTTPAdapter(max_retries=3)) # Retry yerine sabit deneme sayısı kullanıldı

# Token sayacı
total_tokens = 0


@app.route("/chat", methods=["POST"])
def chat():
    """Chat mesajı alır ve kaydeder."""
    global total_tokens
    try:
        data = request.get_json()
        birth_info_id = session.get("birth_info_id")

        # Load astro_data from filesystem if it exists
        astro_data = None
        if birth_info_id:
            session_file = os.path.join(
                current_app.config["SESSION_FILE_DIR"],
                f"astro_data_{birth_info_id}.json",
            )
            if os.path.exists(session_file):
                with open(session_file, "r") as f:
                    astro_data = json.load(f)
        name = session.get("name", "Anonim")
        message = data.get("message")
        is_first_message = data.get("is_first_message", False)

        # En son analizi al
        if is_first_message:
            # Doğum bilgilerini doğrudan kullan
            birth_info_data = session.get(f"astro_data_{birth_info_id}", {}).get("birth_info", {})
            planet_positions_data = session.get(f"astro_data_{birth_info_id}", {}).get("planet_positions", {})
            houses_data = session.get(f"astro_data_{birth_info_id}", {}).get("houses", {})
            transit_positions_data = session.get(f"astro_data_{birth_info_id}", {}).get("transit_positions", {})

            system_prompt = f"""Sen bir astroloji uzmanısın. Aşağıdaki natal harita verilerine göre soruları yanıtla:

            Danışan: {name}
            Doğum Bilgileri: {birth_info_data}
            
            Gezegen Pozisyonları: {planet_positions_data}
            Yükselen Burç: {houses_data.get("important_angles", {}).get("ascendant")}
            Transit Pozisyonlar: {transit_positions_data}
            
            Yukarıdaki bilgileri kullanarak soruları yanıtla. Her yanıtta ilgili gezegen pozisyonlarına atıfta bulun.
            """
            message = system_prompt

        # API isteği - global session yerine http_session kullan
        response = http_session.post(
            "https://api.hyperbolic.xyz/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {HYPERBOLIC_API_KEY}",
            },
            json={
                "model": "deepseek-ai/DeepSeek-V3",
                "messages": [
                    {"role": "system", "content": "Sen uzman bir astrologsun."},
                    {"role": "user", "content": message},
                ],
                "temperature": 0.7,
                "max_tokens": 1000,
            },
        )

        if response.status_code == 200:
            ai_response = response.json()
            response_text = ai_response["choices"][0]["message"]["content"]

            # Token kullanımını hesapla ve logla
            prompt_tokens = ai_response.get("usage", {}).get("prompt_tokens", 0)
            completion_tokens = ai_response.get("usage", {}).get("completion_tokens", 0)
            total_tokens += prompt_tokens + completion_tokens

            logging.info(
                f"Token Kullanımı - Prompt: {prompt_tokens}, "
                f"Completion: {completion_tokens}, "
                f"Toplam: {total_tokens}"
            )

            return jsonify({"status": "success", "response": response_text})

        else:
            raise ValueError(f"API Hatası: {response.status_code}")

    except Exception as e:
        logging.error(f"Chat hatası: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500


# Global değişkenler
location_service = None
_services_initialized = False
logger = logging.getLogger(__name__)


@app.before_request
def initialize_services():
    global location_service, _services_initialized
    if not _services_initialized:
        try:
            location_service = LocationService(
                api_key=app.config.get("OPENCAGE_API_KEY")
            )
            _services_initialized = True
            logger.info("Location service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize location service: {str(e)}")




if __name__ == "__main__":
    app.run(debug=True, port=8088)
