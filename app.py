import os
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

from src.config import config
from src.services.fitness_simulator import FitnessSimulator


def create_app(config_name="default"):

    app = Flask(
        __name__,
        template_folder="src/templates",
        static_folder="src/static"
    )

    # -------------------------------
    # CARGAR CONFIGURACIÓN
    # -------------------------------
    app_config_class = config[config_name]
    app_config = app_config_class()
    app.config.from_object(app_config)
    app.config["APP_CONFIG"] = app_config

    # -------------------------------
    # CONECTAR A MONGO
    # -------------------------------
    try:
        client = MongoClient(
            app.config["MONGO_URI"],
            server_api=ServerApi("1"),
            tlsAllowInvalidCertificates=True
        )
        client.admin.command("ping")

        app.db = client.get_database()
        print("✅ Conexión exitosa a MongoDB Atlas")

        # INICIAR SIMULADOR BIOMÉTRICO
        app.simulator = FitnessSimulator(app.db, app_config)
        app.simulator.start()
        print("🏃 Simulador de fitness tracker iniciado")

    except Exception as e:
        print(f"❌ Error conectando a MongoDB: {e}")
        app.db = None
        app.simulator = None

    # ==========================================
    #                RUTAS WEB
    # ==========================================

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/metrics")
    def metrics():
        return render_template("metrics.html")

    @app.route("/about")
    def about():
        return render_template("about.html")

    # ==========================================
    #         API BIOMÉTRICOS (TU SIMULADOR)
    # ==========================================

    @app.route("/api/biometrics/latest")
    def api_latest():
        latest = app.db.biometric_readings.find_one(sort=[("timestamp", -1)])
        if not latest:
            return jsonify({"message": "No data available"}), 404

        latest["_id"] = str(latest["_id"])
        return jsonify(latest)

    @app.route("/api/biometrics/history")
    def api_history():
        history = list(app.db.biometric_readings.find().sort("timestamp", -1).limit(50))
        for h in history:
            h["_id"] = str(h["_id"])
        return jsonify(history)

    @app.route("/api/steps/total")
    def api_steps():
        latest = app.db.biometric_readings.find_one(sort=[("timestamp", -1)])
        return jsonify({"total_steps": latest.get("pasos", 0) if latest else 0})

    @app.route("/api/heart_rate/zone")
    def api_zone():
        latest = app.db.biometric_readings.find_one(sort=[("timestamp", -1)])
        if not latest:
            return jsonify({"message": "No data available"}), 404

        hr = latest["frecuencia_cardiaca"]
        zones = app_config.HEART_RATE_ZONES

        zone = next(
            (name for name, z in zones.items() if z["min"] <= hr < z["max"]),
            "reposo"
        )

        return jsonify({
            "heart_rate": hr,
            "zone": zone,
            "color": zones[zone]["color"]
        })

    @app.route("/api/simulator/status")
    def api_sim_status():
        return jsonify(app.simulator.get_status())

    @app.route("/api/simulator/reset-steps", methods=["POST"])
    def api_reset():
        app.simulator.reset_steps()
        return jsonify({"message": "Steps reset successfully", "total_steps": 0})

    # ==========================================
    #              API SENSOR EXTERNO
    # ==========================================

    @app.route("/api/sensor/proximidad", methods=["POST"])
    def api_sensor_proximidad():
        """Recibe datos enviados desde sensor_simulado.py"""

        data = request.json

        if not data:
            return jsonify({"error": "No data received"}), 400

        try:
            app.db.sensor_data.insert_one({
                "sensor_id": data.get("sensor_id"),
                "distancia_cm": data.get("distancia_cm"),
                "timestamp": datetime.utcnow()
            })

            print(f"📩 Dato recibido y guardado: {data}")

            return jsonify({"status": "ok", "received": data}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return app


# ==========================================
# EJECUTAR APP
# ==========================================
if __name__ == "__main__":
    env = os.getenv("FLASK_ENV", "development")
    app = create_app(env)
    app.run(host="0.0.0.0", port=5000, debug=app.config["DEBUG"])
