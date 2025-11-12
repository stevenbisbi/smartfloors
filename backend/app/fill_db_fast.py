import requests
import random
from datetime import datetime, timedelta

API_URL = "http://localhost:8000/api/data"  # Cambia si tu endpoint es distinto
PISOS = [1, 2, 3]

# Config base por piso
FLOOR_CONFIGS = {
    1: {"temp": (21, 26), "humedad": (40, 70), "energia": (8, 15)},
    2: {"temp": (23, 28), "humedad": (45, 75), "energia": (10, 18)},
    3: {"temp": (25, 30), "humedad": (35, 65), "energia": (12, 20)},
}

def generate_random_data(piso, timestamp):
    """Genera un registro de datos aleatorios para un piso."""
    cfg = FLOOR_CONFIGS[piso]
    return {
        "timestamp": timestamp.isoformat(),
        "edificio": "A",
        "piso": piso,
        "temp_C": round(random.uniform(*cfg["temp"]), 2),
        "humedad_pct": round(random.uniform(*cfg["humedad"]), 2),
        "energia_kW": round(random.uniform(*cfg["energia"]), 2)
    }

def fill_database(n_registros=300, minutos_intervalo=1):
    """
    Envía n_registros por piso con intervalos de tiempo simulados.
    - n_registros: cantidad total de registros por piso
    - minutos_intervalo: tiempo simulado entre lecturas
    """
    print(f"📊 Enviando {n_registros * len(PISOS)} registros al servidor...")
    start_time = datetime.now() - timedelta(minutes=n_registros * minutos_intervalo)

    enviados = 0
    for i in range(n_registros):
        timestamp = start_time + timedelta(minutes=i * minutos_intervalo)

        for piso in PISOS:
            data = generate_random_data(piso, timestamp)

            try:
                response = requests.post(API_URL, json=data)
                if response.status_code == 201:
                    enviados += 1
                    print(f"✓ Piso {piso} | {data['timestamp']} | "
                          f"T={data['temp_C']}°C H={data['humedad_pct']}% E={data['energia_kW']}kW")
                else:
                    print(f"✗ Error {response.status_code}: {response.text}")

            except Exception as e:
                print(f"⚠️ Error al conectar: {e}")
    
    print(f"\n✅ Carga completada: {enviados} registros enviados exitosamente.")

if __name__ == "__main__":
    # Puedes ajustar los valores aquí:
    fill_database(
        n_registros=500,  # número de registros por piso
        minutos_intervalo=2  # minutos simulados entre lecturas
    )
