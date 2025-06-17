import paho.mqtt.client as mqtt
import logging
import time

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MQTTLogger")

# Configurações do MQTT
BROKER = "cjsg.ddns.net"  # ou o IP do teu broker local
PORT = 1883
TOPIC = "/weather"
USERNAME = "cd"
PASSWORD = "1qaz\"WSX"
CLIENT_ID = f"mqtt_logger_{int(time.time())}"

# === Funções de callback ===
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info(f"✅ Conectado ao broker MQTT: {BROKER}:{PORT}")
        client.subscribe(TOPIC)
        logger.info(f"📡 Inscrito no tópico: {TOPIC}")
    else:
        logger.error(f"❌ Falha na conexão. Código de retorno: {rc}")

def on_disconnect(client, userdata, rc):
    logger.warning(f"🔌 Desconectado do broker. Código: {rc}")

def on_message(client, userdata, msg):
    logger.info(f"📥 Mensagem recebida no tópico {msg.topic}: {msg.payload.decode('utf-8')}")

def on_subscribe(client, userdata, mid, granted_qos):
    logger.info(f"📶 Subscreveu com sucesso. QoS: {granted_qos}")

def on_log(client, userdata, level, buf):
    logger.debug(f"[LOG MQTT] {buf}")

# === Criar cliente MQTT ===
client = mqtt.Client(client_id=CLIENT_ID, protocol=mqtt.MQTTv311)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.on_subscribe = on_subscribe
# client.on_log = on_log  # Ativa se quiser logs detalhados do protocolo

# === Conectar e iniciar loop ===
try:
    logger.info("🚀 A tentar conectar...")
    client.connect(BROKER, PORT, USERNAME ,PASSWORD,keepalive=60)
    client.loop_start()

    # Mantém o script a correr
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    logger.info("🛑 Encerrando conexão com MQTT...")
    client.loop_stop()
    client.disconnect()
