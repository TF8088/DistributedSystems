import paho.mqtt.client as mqtt
import json
import time
import random
from datetime import datetime

# Configurações do broker MQTT
BROKER = "broker.emqx.io"
PORT = 1883
TOPIC = "/weather"
CLIENT_ID = f"publisher_{random.randint(1000, 9999)}"

# Função para criar dados meteorológicos simulados
def generate_weather_data():
    temperatura = round(random.uniform(15.0, 30.0), 1)  # Temperatura entre 15°C e 30°C
    humidade = round(random.uniform(50.0, 90.0), 1)    # Humidade entre 50% e 90%
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return {
        "temperatura": temperatura,
        "humidade": humidade,
        "timestamp": timestamp
    }

# Callback para quando o cliente se conecta ao broker
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Conectado ao broker MQTT")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Falha na conexão, código: {rc}")

# Função principal para publicar dados
def publish_data():
    client = mqtt.Client(client_id=CLIENT_ID, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect

    try:
        client.connect(BROKER, PORT, keepalive=60)
        client.loop_start()

        while True:
            data = generate_weather_data()
            payload = json.dumps(data)
            result = client.publish(TOPIC, payload, qos=2)
            status = result[0]
            if status == 0:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Publicado: {payload}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Falha ao publicar mensagem")
            time.sleep(10)  # Publica a cada 10 segundos

    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Erro: {e}")
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    print(f"Iniciando publicador MQTT para {BROKER}:{PORT}, tópico: {TOPIC}")
    publish_data()