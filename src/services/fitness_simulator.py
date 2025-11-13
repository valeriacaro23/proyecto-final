import random
import time
import threading
from datetime import datetime
from typing import Optional
from pymongo.database import Database
from src.model.biometric import BiometricReading
from src.config import Config

class FitnessSimulator:
    """
    Simulador de dispositivo wearable (smartwatch/fitness tracker)
    Genera datos realistas de sensores biométricos
    """
    
    def __init__(self, db: Database, config: Config):
        """
        Inicializar el simulador
        
        Args:
            db: Base de datos MongoDB
            config: Configuración de la aplicación
        """
        self.db = db
        self.config = config
        self.is_running = False
        self.thread: Optional[threading.Thread] = None
        
        # Estado del usuario (simula diferentes niveles de actividad)
        self.activity_state = 'resting'  # resting, light, moderate, intense
        self.total_steps = 0
        self.baseline_hr = 75  # Frecuencia cardíaca base
        
        # Configuración de sensores
        self.sensors_config = config.SENSORS
    
    def _generate_heart_rate(self) -> int:
        """Generar frecuencia cardíaca según el estado de actividad"""
        base_hr = self.baseline_hr
        
        # Ajustar según actividad
        if self.activity_state == 'resting':
            target_hr = random.randint(60, 80)
        elif self.activity_state == 'light':
            target_hr = random.randint(90, 110)
        elif self.activity_state == 'moderate':
            target_hr = random.randint(120, 140)
        elif self.activity_state == 'intense':
            target_hr = random.randint(150, 175)
        else:
            target_hr = base_hr
        
        # Añadir variación natural (±5 bpm)
        hr = target_hr + random.randint(-5, 5)
        
        # Asegurar que esté en rango válido
        hr = max(self.sensors_config['frecuencia_cardiaca']['min'], 
                 min(hr, self.sensors_config['frecuencia_cardiaca']['max']))
        
        return hr
    
    def _generate_steps(self) -> int:
        """Generar pasos según el estado de actividad"""
        # Incremento de pasos según actividad
        if self.activity_state == 'resting':
            increment = random.randint(0, 2)
        elif self.activity_state == 'light':
            increment = random.randint(3, 8)
        elif self.activity_state == 'moderate':
            increment = random.randint(10, 20)
        elif self.activity_state == 'intense':
            increment = random.randint(25, 40)
        else:
            increment = 0
        
        self.total_steps += increment
        return self.total_steps
    
    def _generate_oxygen(self) -> float:
        """Generar saturación de oxígeno"""
        # Durante ejercicio intenso, puede bajar ligeramente
        if self.activity_state == 'intense':
            base_spo2 = random.uniform(95.0, 98.0)
        else:
            base_spo2 = random.uniform(97.0, 100.0)
        
        # Añadir variación mínima
        spo2 = base_spo2 + random.uniform(-0.5, 0.5)
        
        # Asegurar que esté en rango válido
        spo2 = max(self.sensors_config['oxigeno']['min'], 
                   min(spo2, self.sensors_config['oxigeno']['max']))
        
        return round(spo2, 1)
    
    def _generate_temperature(self) -> float:
        """Generar temperatura corporal"""
        # Temperatura aumenta con la actividad
        if self.activity_state == 'resting':
            base_temp = random.uniform(36.3, 36.8)
        elif self.activity_state == 'light':
            base_temp = random.uniform(36.6, 37.0)
        elif self.activity_state == 'moderate':
            base_temp = random.uniform(36.9, 37.3)
        elif self.activity_state == 'intense':
            base_temp = random.uniform(37.0, 37.5)
        else:
            base_temp = 36.6
        
        # Añadir variación mínima
        temp = base_temp + random.uniform(-0.1, 0.1)
        
        # Asegurar que esté en rango válido
        temp = max(self.sensors_config['temperatura']['min'], 
                   min(temp, self.sensors_config['temperatura']['max']))
        
        return round(temp, 1)
    
    def _change_activity_state(self):
        """Cambiar aleatoriamente el estado de actividad para simular comportamiento real"""
        states = ['resting', 'light', 'moderate', 'intense']
        weights = [0.4, 0.3, 0.2, 0.1]  # Mayor probabilidad de reposo
        
        # Cambiar estado ocasionalmente (20% de probabilidad)
        if random.random() < 0.2:
            self.activity_state = random.choices(states, weights=weights)[0]
            print(f"🏃 Estado de actividad cambiado a: {self.activity_state}")
    
    def generate_reading(self) -> BiometricReading:
        """Generar una lectura biométrica completa"""
        # Ocasionalmente cambiar el estado de actividad
        self._change_activity_state()
        
        # Generar datos de todos los sensores
        hr = self._generate_heart_rate()
        steps = self._generate_steps()
        spo2 = self._generate_oxygen()
        temp = self._generate_temperature()
        
        # Crear lectura
        reading = BiometricReading(
            frecuencia_cardiaca=hr,
            pasos=steps,
            oxigeno=spo2,
            temperatura=temp,
            timestamp=datetime.utcnow()
        )
        
        return reading
    
    def save_reading(self, reading: BiometricReading):
        """Guardar lectura en MongoDB"""
        try:
            result = self.db.biometric_readings.insert_one(reading.to_dict())
            print(f"✅ Lectura guardada: {reading}")
            return result.inserted_id
        except Exception as e:
            print(f"❌ Error guardando lectura: {e}")
            return None
    
    def _simulation_loop(self):
        """Loop principal de simulación"""
        print("🚀 Simulador de fitness tracker iniciado")
        print(f"📊 Generando lecturas cada {self.config.DEVICE_INTERVAL} segundos")
        
        while self.is_running:
            try:
                # Generar y guardar lectura
                reading = self.generate_reading()
                self.save_reading(reading)
                
                # Mostrar estado de salud
                health_status = reading.get_health_status()
                print(f"💓 Estado: {health_status['overall']} | Zona FC: {reading.get_heart_rate_zone()}")
                
                # Esperar antes de la siguiente lectura
                time.sleep(self.config.DEVICE_INTERVAL)
                
            except Exception as e:
                print(f"❌ Error en simulación: {e}")
                time.sleep(self.config.DEVICE_INTERVAL)
    
    def start(self):
        """Iniciar el simulador en un thread separado"""
        if self.is_running:
            print("⚠️ El simulador ya está en ejecución")
            return
        
        self.is_running = True
        self.thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.thread.start()
        print("✅ Simulador iniciado correctamente")
    
    def stop(self):
        """Detener el simulador"""
        if not self.is_running:
            print("⚠️ El simulador no está en ejecución")
            return
        
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("🛑 Simulador detenido")
    
    def reset_steps(self):
        """Resetear contador de pasos (simula inicio de nuevo día)"""
        self.total_steps = 0
        print("🔄 Contador de pasos reseteado")
    
    def get_status(self) -> dict:
        """Obtener estado actual del simulador"""
        return {
            'running': self.is_running,
            'activity_state': self.activity_state,
            'total_steps': self.total_steps,
            'baseline_hr': self.baseline_hr,
            'interval': self.config.DEVICE_INTERVAL
        }