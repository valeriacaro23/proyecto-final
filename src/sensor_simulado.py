import time
import json
import random
import requests

# URL del endpoint Flask que va a recibir los datos
SERVER_URL = "http://127.0.0.1:5000/api/sensor/proximidad"

def generar_lectura():
    """Simula un sensor de proximidad"""
    return {
        "sensor_id": "proximidad_01",
        "distancia_cm": round(random.uniform(5.0, 40.0), 2)
    }

def enviar_dato():
    """Envía una lectura al servidor Flask via POST"""
    data = generar_lectura()
    try:
        response = requests.post(SERVER_URL, json=data)
        print(f"📡 Enviado: {data} | Respuesta: {response.status_code}")
    except Exception as e:
        print(f"❌ Error enviando datos: {e}")

def iniciar_simulacion(intervalo=5):
    """Loop infinito simulando el microcontrolador"""
    print("🔵 Simulación de sensor iniciada...")
    while True:
        enviar_dato()
        time.sleep(intervalo)

if __name__ == "__main__":
    iniciar_simulacion()
