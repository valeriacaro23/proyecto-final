import os
from flask import Flask, render_template, jsonify
from pymongo import MongoClient
from src.config import config
from src.services.fitness_simulator import FitnessSimulator

def create_app(config_name='default'):
    """Factory para crear la aplicación Flask"""
    
    # Crear instancia de Flask
    app = Flask(__name__, 
                template_folder='src/templates',
                static_folder='src/static')
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Inicializar MongoDB
    try:
        client = MongoClient(app.config['MONGO_URI'])
        app.db = client.get_database()
        print("✅ Conexión exitosa a MongoDB")
    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        app.db = None
    
    # Rutas
    @app.route('/')
    def index():
        """Página principal"""
        return render_template('index.html')
    
    @app.route('/dashboard')
    def dashboard():
        """Dashboard con datos de actividad física"""
        return render_template('dashboard.html')
    
    @app.route('/api/biometrics/latest')
    def get_latest_biometrics():
        """API: Obtener últimas lecturas biométricas"""
        if app.db is None:
            return jsonify({'error': 'Database not connected'}), 500
        
        try:
            # Obtener última lectura
            latest_data = list(app.db.biometric_readings.find().sort('timestamp', -1).limit(1))
            
            if latest_data:
                # Convertir ObjectId a string para JSON
                latest_data[0]['_id'] = str(latest_data[0]['_id'])
                return jsonify(latest_data[0])
            else:
                return jsonify({'message': 'No data available'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/biometrics/history')
    def get_biometrics_history():
        """API: Obtener histórico de lecturas (últimas 50)"""
        if app.db is None:
            return jsonify({'error': 'Database not connected'}), 500
        
        try:
            history = list(app.db.biometric_readings.find().sort('timestamp', -1).limit(50))
            
            # Convertir ObjectId a string
            for reading in history:
                reading['_id'] = str(reading['_id'])
            
            return jsonify(history)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/steps/total')
    def get_total_steps():
        """API: Obtener total de pasos del día"""
        if app.db is None:
            return jsonify({'error': 'Database not connected'}), 500
        
        try:
            # Obtener la última lectura que contiene el total acumulado
            latest = app.db.biometric_readings.find_one(sort=[('timestamp', -1)])
            
            if latest and 'pasos' in latest:
                return jsonify({'total_steps': latest['pasos']})
            else:
                return jsonify({'total_steps': 0})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/heart_rate/zone')
    def get_heart_rate_zone():
        """API: Obtener zona de frecuencia cardíaca actual"""
        if app.db is None:
            return jsonify({'error': 'Database not connected'}), 500
        
        try:
            latest = app.db.biometric_readings.find_one(sort=[('timestamp', -1)])
            
            if latest and 'frecuencia_cardiaca' in latest:
                hr = latest['frecuencia_cardiaca']
                zone = 'reposo'
                
                # Determinar zona
                for zone_name, zone_data in app.config['HEART_RATE_ZONES'].items():
                    if zone_data['min'] <= hr < zone_data['max']:
                        zone = zone_name
                        break
                
                return jsonify({
                    'heart_rate': hr,
                    'zone': zone,
                    'color': app.config['HEART_RATE_ZONES'][zone]['color']
                })
            else:
                return jsonify({'message': 'No data available'}), 404
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @app.route('/about')
    def about():
        """Página sobre el proyecto"""
        return render_template('about.html')
    
    return app


if __name__ == '__main__':
    # Determinar el entorno
    env = os.getenv('FLASK_ENV', 'development')
    
    # Crear aplicación
    app = create_app(env)
    
    # Ejecutar servidor
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])