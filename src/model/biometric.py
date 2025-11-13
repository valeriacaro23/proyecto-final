from datetime import datetime
from typing import Dict, Any

class BiometricReading:
    """Modelo para una lectura biométrica del dispositivo wearable"""
    
    def __init__(self, 
                 frecuencia_cardiaca: int,
                 pasos: int,
                 oxigeno: float,
                 temperatura: float,
                 timestamp: datetime = None):
        """
        Inicializar una lectura biométrica
        
        Args:
            frecuencia_cardiaca: Frecuencia cardíaca en bpm
            pasos: Total de pasos acumulados
            oxigeno: Saturación de oxígeno en %
            temperatura: Temperatura corporal en °C
            timestamp: Momento de la lectura (por defecto ahora)
        """
        self.frecuencia_cardiaca = frecuencia_cardiaca
        self.pasos = pasos
        self.oxigeno = oxigeno
        self.temperatura = temperatura
        self.timestamp = timestamp or datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir la lectura a diccionario para MongoDB"""
        return {
            'frecuencia_cardiaca': self.frecuencia_cardiaca,
            'pasos': self.pasos,
            'oxigeno': self.oxigeno,
            'temperatura': self.temperatura,
            'timestamp': self.timestamp,
            'metadata': {
                'device_type': 'ESP32_Wearable',
                'firmware_version': '1.0.0',
                'sensor_status': 'active'
            }
        }
    
    def __str__(self) -> str:
        """Representación en string de la lectura"""
        return (f"BiometricReading(FC={self.frecuencia_cardiaca}bpm, "
                f"Pasos={self.pasos}, SpO2={self.oxigeno}%, "
                f"Temp={self.temperatura}°C, Time={self.timestamp})")
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'BiometricReading':
        """Crear una lectura desde un diccionario"""
        return BiometricReading(
            frecuencia_cardiaca=data['frecuencia_cardiaca'],
            pasos=data['pasos'],
            oxigeno=data['oxigeno'],
            temperatura=data['temperatura'],
            timestamp=data.get('timestamp', datetime.utcnow())
        )
    
    def get_heart_rate_zone(self) -> str:
        """Determinar la zona de frecuencia cardíaca"""
        hr = self.frecuencia_cardiaca
        
        if hr < 60:
            return 'reposo'
        elif hr < 100:
            return 'ligera'
        elif hr < 140:
            return 'moderada'
        elif hr < 170:
            return 'intensa'
        else:
            return 'maxima'
    
    def is_oxygen_normal(self) -> bool:
        """Verificar si el nivel de oxígeno es normal"""
        return self.oxigeno >= 95.0
    
    def is_temperature_normal(self) -> bool:
        """Verificar si la temperatura corporal es normal"""
        return 36.1 <= self.temperatura <= 37.5
    
    def get_health_status(self) -> Dict[str, str]:
        """Obtener el estado general de salud basado en las métricas"""
        status = {
            'heart_rate': 'normal',
            'oxygen': 'normal',
            'temperature': 'normal',
            'overall': 'healthy'
        }
        
        # Evaluar frecuencia cardíaca
        zone = self.get_heart_rate_zone()
        if zone in ['intensa', 'maxima']:
            status['heart_rate'] = 'elevated'
        
        # Evaluar oxígeno
        if not self.is_oxygen_normal():
            status['oxygen'] = 'low' if self.oxigeno >= 90 else 'critical'
        
        # Evaluar temperatura
        if not self.is_temperature_normal():
            status['temperature'] = 'abnormal'
        
        # Estado general
        if any(v in ['low', 'critical', 'abnormal'] for v in status.values()):
            status['overall'] = 'attention_needed'
        elif status['heart_rate'] == 'elevated':
            status['overall'] = 'exercising'
        
        return status