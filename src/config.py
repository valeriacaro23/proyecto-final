import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    """Configuración base de la aplicación"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'True') == 'True'
    
    # MongoDB
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://admin:admin123@localhost:27017/fitness_tracker_db?authSource=admin')
    
    # Simulación de dispositivo wearable
    DEVICE_INTERVAL = int(os.getenv('DEVICE_INTERVAL', 5))  # Segundos entre lecturas
    
    # Configuración de sensores biométricos (valores para simulación)
    SENSORS = {
        'frecuencia_cardiaca': {
            'min': 60,      # bpm en reposo
            'max': 180,     # bpm máximo durante ejercicio
            'normal': 75,   # bpm normal
            'unit': 'bpm'
        },
        'pasos': {
            'increment_min': 0,   # Pasos mínimos por lectura
            'increment_max': 15,  # Pasos máximos por lectura
            'unit': 'pasos'
        },
        'oxigeno': {
            'min': 95.0,    # % SpO2 mínimo saludable
            'max': 100.0,   # % SpO2 máximo
            'normal': 98.0, # % SpO2 normal
            'unit': '%'
        },
        'temperatura': {
            'min': 36.1,    # °C temperatura corporal mínima
            'max': 37.5,    # °C temperatura corporal máxima
            'normal': 36.6, # °C temperatura normal
            'unit': '°C'
        }
    }
    
    # Zonas de frecuencia cardíaca (basadas en % de FC máxima)
    HEART_RATE_ZONES = {
        'reposo': {'min': 0, 'max': 60, 'color': '#6b7280'},
        'ligera': {'min': 60, 'max': 100, 'color': '#10b981'},
        'moderada': {'min': 100, 'max': 140, 'color': '#f59e0b'},
        'intensa': {'min': 140, 'max': 170, 'color': '#ef4444'},
        'maxima': {'min': 170, 'max': 220, 'color': '#dc2626'}
    }
    
    @staticmethod
    def init_app(app):
        """Inicializar configuración adicional si es necesario"""
        pass


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False


# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}