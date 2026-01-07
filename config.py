import os
from pathlib import Path
from env_config import EnvConfig, get_env_required, get_env


class Config:
    """
    Flask Configuration with secure environment variable handling.
    
    All sensitive values are loaded from environment variables with proper
    validation. No hardcoded secrets in production code.
    """
    
    # Flask Secret Key - REQUIRED for production security
    SECRET_KEY = get_env("SECRET_KEY", "dev-secret-key-placeholder")
    
    # Database Configuration
    IS_SERVERLESS = os.environ.get("VERCEL") or os.environ.get("NETLIFY") or os.environ.get("GAE_SERVICE")
    if IS_SERVERLESS:
        DEFAULT_DB = "sqlite:////tmp/astro.db"
    else:
        DEFAULT_DB = "sqlite:///instance/astro.db"
        
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", DEFAULT_DB)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys - Loaded securely from environment
    OPENCAGE_API_KEY = get_env_required("OPENCAGE_API_KEY")
    HYPERBOLIC_API_KEY = get_env("HYPERBOLIC_API_KEY", "")
    HYPERBOLIC_API_URL = "https://api.hyperbolic.xyz/v1/chat/completions"
    HYPERBOLIC_MODEL = "deepseek-ai/DeepSeek-V3"
    GEMINI_API_KEY = get_env("GOOGLE_API_KEY", "")  # Alias for GOOGLE_API_KEY
    
    # Additional AI API Keys
    GOOGLE_API_KEY = get_env("GOOGLE_API_KEY", "")
    OPENROUTER_API_KEY = get_env("OPENROUTER_API_KEY", "")
    
    # Supabase Configuration - Loaded from environment
    SUPABASE_URL = get_env("SUPABASE_URL", "")
    SUPABASE_KEY = get_env("SUPABASE_KEY", "")
    SUPABASE_SERVICE_KEY = get_env("SUPABASE_SERVICE_KEY", "")
    
    # Session Configuration - Dynamically set based on environment
    SESSION_TYPE = os.getenv("SESSION_TYPE", "filesystem")  # Will be 'redis' in Task 3
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = int(os.getenv("SESSION_LIFETIME_HOURS", "1")) * 3600
    SESSION_USE_SIGNER = True
    SESSION_COOKIE_SECURE = EnvConfig.get_session_cookie_secure()
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "astro_session")
    
    # Redis Configuration (for session storage and caching)
    REDIS_HOST = get_env("REDIS_HOST", "localhost")
    REDIS_PORT = int(get_env("REDIS_PORT", "6379"))
    REDIS_DB = get_env("REDIS_DB", "0")
    REDIS_PASSWORD = get_env("REDIS_PASSWORD", "")
    
    # Cache Configuration
    CACHE_TYPE = os.getenv("CACHE_TYPE", "simple")  # Will be 'redis' in Task 7
    CACHE_REDIS_HOST = REDIS_HOST
    CACHE_REDIS_PORT = REDIS_PORT
    CACHE_REDIS_DB = REDIS_DB
    CACHE_REDIS_PASSWORD = REDIS_PASSWORD
    CACHE_DEFAULT_TIMEOUT = int(os.getenv("CACHE_DEFAULT_TIMEOUT", "3600"))  # 1 hour
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Feature Flags
    ENABLE_AI_INTERPRETATIONS = os.getenv("ENABLE_AI_INTERPRETATIONS", "True").lower() == "true"
    ENABLE_TTS = os.getenv("ENABLE_TTS", "True").lower() == "true"
    ENABLE_CACHE = os.getenv("ENABLE_CACHE", "True").lower() == "true"
    
    @staticmethod
    def init_app(app):
        """Initialize configuration with environment validation."""
        # Validate and initialize environment configuration
        EnvConfig.initialize()
        
        # Set logging level
        import logging
        log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
        app.logger.setLevel(log_level)
        
        # Log configuration status (without exposing secrets)
        app.logger.info(f"Application initialized in {EnvConfig.get_optional('FLASK_ENV', 'development')} mode")
        app.logger.info(f"Session cookie secure: {Config.SESSION_COOKIE_SECURE}")
        app.logger.info(f"Session type: {Config.SESSION_TYPE}")


class DevelopmentConfig(Config):
    """Development configuration with relaxed security for local development."""
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development


class ProductionConfig(Config):
    """Production configuration with enhanced security."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    # Ensure all required variables are set
    def __init__(self):
        EnvConfig.validate_required()


class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    # Use in-memory cache for testing
    CACHE_TYPE = "simple"


# Configuration dictionary
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}


def get_config(env_name=None):
    """
    Get configuration class based on environment name.
    
    Args:
        env_name: Environment name (development, production, testing).
                 If None, reads from FLASK_ENV environment variable.
    
    Returns:
        Configuration class.
    """
    if env_name is None:
        env_name = os.getenv("FLASK_ENV", "development")
    
    return config.get(env_name, DevelopmentConfig)
