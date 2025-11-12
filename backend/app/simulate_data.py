import requests
import random
import time
from datetime import datetime
import json

# Configuración
API_URL = "http://localhost:8000/api/data"
PISOS = [1, 2, 3]

# Rangos base para cada piso (puedes ajustar para simular diferentes condiciones)
FLOOR_CONFIGS = {
    1: {
        "temp_base": 23.0,
        "temp_var": 3.0,
        "humedad_base": 50.0,
        "humedad_var": 15.0,
        "energia_base": 10.0,
        "energia_var": 5.0
    },
    2: {
        "temp_base": 25.0,
        "temp_var": 4.0,  # Más variación en piso 2
        "humedad_base": 55.0,
        "humedad_var": 20.0,
        "energia_base": 12.0,
        "energia_var": 7.0
    },
    3: {
        "temp_base": 27.0,  # Piso 3 tiende a ser más caliente
        "temp_var": 3.5,
        "humedad_base": 45.0,
        "humedad_var": 12.0,
        "energia_base": 14.0,
        "energia_var": 6.0
    }
}

def generate_reading(piso: int, trend_factor: float = 0) -> dict:
    """
    Genera una lectura simulada para un piso
    trend_factor: factor de tendencia (-1 a 1) para simular cambios graduales
    """
    config = FLOOR_CONFIGS[piso]
    
    # Añadir tendencia gradual para hacer más realista
    temp = config["temp_base"] + random.uniform(-config["temp_var"], config["temp_var"]) + trend_factor
    humedad = config["humedad_base"] + random.uniform(-config["humedad_var"], config["humedad_var"])
    energia = config["energia_base"] + random.uniform(-config["energia_var"], config["energia_var"])
    
    # Asegurar que los valores estén en rangos válidos
    humedad = max(0, min(100, humedad))
    energia = max(0, energia)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "edificio": "A",
        "piso": piso,
        "temp_C": round(temp, 2),
        "humedad_pct": round(humedad, 2),
        "energia_kW": round(energia, 2)
    }

def simulate_scenario(scenario: str = "normal"):
    """
    Simula diferentes escenarios
    - normal: condiciones normales
    - alert: genera condiciones que disparan alertas
    - spike: genera un pico repentino
    """
    readings = []
    
    if scenario == "normal":
        for piso in PISOS:
            readings.append(generate_reading(piso))
    
    elif scenario == "alert":
        # Simular condiciones de alerta en piso 2
        for piso in PISOS:
            if piso == 2:
                reading = generate_reading(piso)
                reading["temp_C"] = 29.0  # Temperatura alta
                reading["energia_kW"] = 18.0  # Energía alta
                readings.append(reading)
            else:
                readings.append(generate_reading(piso))
    
    elif scenario == "spike":
        # Simular pico en piso 3
        for piso in PISOS:
            if piso == 3:
                reading = generate_reading(piso)
                reading["temp_C"] = 31.0  # Temperatura crítica
                reading["humedad_pct"] = 75.0  # Humedad alta
                reading["energia_kW"] = 22.0  # Energía crítica
                readings.append(reading)
            else:
                readings.append(generate_reading(piso))
    
    return readings

def send_data(reading: dict):
    """
    Envía un registro al API
    """
    try:
        response = requests.post(API_URL, json=reading)
        if response.status_code == 201:
            print(f"✓ Piso {reading['piso']}: T={reading['temp_C']}°C, H={reading['humedad_pct']}%, E={reading['energia_kW']}kW")
        else:
            print(f"✗ Error al enviar datos del piso {reading['piso']}: {response.status_code}")
    except Exception as e:
        print(f"✗ Error de conexión: {e}")

def main():
    print("=== SmartFloors - Simulador de Datos ===")
    print("Enviando datos cada 60 segundos...")
    print("Presiona Ctrl+C para detener\n")
    
    iteration = 0
    trend = 0
    
    try:
        while True:
            iteration += 1
            print(f"\n--- Iteración {iteration} - {datetime.now().strftime('%H:%M:%S')} ---")
            
            # Cada 10 iteraciones, cambiar el escenario para hacer más interesante
            if iteration % 20 == 0:
                scenario = "alert"
                print("⚠️  Simulando condiciones de ALERTA")
            elif iteration % 30 == 0:
                scenario = "spike"
                print("🔥 Simulando PICO crítico")
            else:
                scenario = "normal"
            
            # Generar y enviar datos
            readings = simulate_scenario(scenario)
            
            for reading in readings:
                send_data(reading)
            
            # Pequeña tendencia para hacer más realista
            trend = random.uniform(-0.5, 0.5)
            
            # Esperar 60 segundos (o ajusta según necesites)
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\n✓ Simulador detenido")

if __name__ == "__main__":
    # Opción: ejecutar en modo rápido para testing (cada 5 segundos)
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--fast":
        print("Modo RÁPIDO: datos cada 5 segundos")
        time.sleep = lambda x: time.sleep(5) if x == 60 else time.sleep(x)
    
    main()