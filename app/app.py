from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import json
import time
import secrets
import os
import logging
import requests
from functools import wraps
import threading

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger('paho').setLevel(logging.DEBUG)

# Inicialização do Flask e SocketIO
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurações da API Express
API_BASE_URL = os.getenv('NODE_SERVER_URL', 'http://localhost:3000')

# Configurações MQTT
MQTT_CONFIG_DIR = "mqtt_configs"
MQTT_DEFAULT_CONFIG = os.path.join(MQTT_CONFIG_DIR, "default.json")

# Criar pasta para configurações
if not os.path.exists(MQTT_CONFIG_DIR):
    os.makedirs(MQTT_CONFIG_DIR)

# Cache para dados meteorológicos
cache = {
    "dados": None,
    "timestamp": None,
    "ttl": 60  # Tempo de vida do cache em segundos
}

# === Funções do MQTT ===
mqtt_connected = False
mqtt_client = None

# Função para emitir status via websocket
def emitir_status_mqtt(status, mensagem):
    socketio.emit('mqtt_status', {'status': status, 'mensagem': mensagem})

# Função chamada ao conectar
def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        logger.info("Conectado ao broker MQTT!")
        client.subscribe(MQTT_TOPIC)
        emitir_status_mqtt('conectado', 'Conectado ao broker MQTT!')
    else:
        mqtt_connected = False
        logger.error(f"Falha ao conectar ao broker MQTT: código {rc}")
        emitir_status_mqtt('erro', f'Falha ao conectar ao broker MQTT: código {rc}')

# Função chamada ao receber mensagem
def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        logger.info(f"Mensagem recebida no tópico {msg.topic}: {payload}")
        # Tenta converter o payload em JSON para enviar como objeto ao front-end
        try:
            dados = json.loads(payload)
            # Atualiza o cache para novos clientes WebSocket
            cache["dados"] = dados
            cache["timestamp"] = time.time()
            socketio.emit('atualizacao_dados', dados)
        except Exception as e:
            logger.warning(f"Payload não é JSON válido: {e}")
            # Envia como string mesmo assim
            socketio.emit('atualizacao_dados', payload)
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")

def carregar_config_mqtt():
    """Carrega as configurações MQTT do arquivo default.json."""
    try:
        with open(MQTT_DEFAULT_CONFIG, 'r') as f:
            config = json.load(f)
        logger.info(f"Configuração MQTT carregada de {MQTT_DEFAULT_CONFIG}")
        return config
    except Exception as e:
        logger.error(f"Erro ao carregar configuração MQTT: {e}")
        return None

# Função chamada ao desconectar
def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    logger.warning(f"Desconectado do broker MQTT: código {rc}")
    emitir_status_mqtt('desconectado', f'Desconectado do broker MQTT: código {rc}')

# Função simples para conectar ao broker MQTT
def conectar_mqtt(broker, port, topic, username=None, password=None, client_id=None):
    global mqtt_client, MQTT_BROKER, MQTT_PORT, MQTT_TOPIC
    MQTT_BROKER, MQTT_PORT, MQTT_TOPIC = broker, port, topic

    mqtt_client = mqtt.Client(client_id=client_id)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    if username and password:
        mqtt_client.username_pw_set(username, password)

    mqtt_client.connect(broker, port, keepalive=30)
    mqtt_client.loop_start()

def conectar_mqtt_de_arquivo():
    """Carrega as configurações do arquivo e conecta ao broker MQTT."""
    config = carregar_config_mqtt()
    if not config:
        logger.error("Não foi possível carregar as configurações MQTT.")
        return
    broker = config.get('broker')
    port = config.get('port')
    topic = config.get('topic')
    username = config.get('username')
    password = config.get('password')
    client_id = config.get('client_id')
    if not broker or not port or not topic:
        logger.error("Configuração MQTT incompleta.")
        return
    conectar_mqtt(broker, port, topic, username, password, client_id)

conectar_mqtt_de_arquivo()

# === Funções de Autenticação ===
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'utilizador_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# === Rotas Flask ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        try:
            response = requests.post(f"{API_BASE_URL}/api/login", json={'email': email, 'password': senha})
            if response.status_code == 200:
                user = response.json()
                session['utilizador_id'] = user['id']
                session['nome_utilizador'] = user['email'].split('@')[0]
                return redirect(url_for('index'))
            elif response.status_code == 401:
                flash('Email ou senha incorretos', 'erro')
            else:
                flash('Erro ao autenticar', 'erro')
        except requests.RequestException as e:
            logger.error(f"Erro ao chamar API: {e}")
            flash('Erro ao conectar com a API', 'erro')
    return render_template('login.html')

@app.route('/register', methods=['GET'])
def register():
    return render_template('login.html')

@app.route('/registrar', methods=['POST'])
def registrar():
    email = request.form.get('email')
    senha = request.form.get('senha')
    try:
        response = requests.post(f"{API_BASE_URL}/api/users", json={'email': email, 'password': senha})
        if response.status_code == 201:
            flash('Registro realizado com sucesso! Faça login.', 'sucesso')
            return redirect(url_for('login'))
        elif response.status_code == 409:
            flash('Este email já está registrado', 'erro')
        else:
            flash('Erro ao registrar utilizado', 'erro')
    except requests.RequestException as e:
        logger.error(f"Erro ao chamar API: {e}")
        flash('Erro ao conectar com a API', 'erro')
    return render_template('index.html')

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    nome_utilizador = session.get('nome_utilizador', 'utilizado')
    return render_template('index.html', nome_utilizador=nome_utilizador)

@app.route('/api/status-mqtt', methods=['GET'])
def status_mqtt():
    global mqtt_connected
    try:
        if mqtt_client and mqtt_connected:
            return jsonify({
                "status": "conectado",
                "mensagem": f"Conectado ao broker MQTT",
                "broker": MQTT_BROKER,
                "port": MQTT_PORT,
                "topic": MQTT_TOPIC
            }), 200
        else:
            return jsonify({
                "status": "desconectado",
                "mensagem": "Não conectado ao broker MQTT"
            }), 200
    except Exception as e:
        logger.error(f"Erro ao verificar status MQTT: {e}")
        return jsonify({
            "status": "erro",
            "mensagem": f"Erro ao verificar status: {str(e)}"
        }), 500


# === Eventos SocketIO ===
@socketio.on('connect')
def handle_connect():
    global mqtt_connected
    if 'utilizador_id' in session:
        logger.info(f"Cliente WebSocket conectado: {request.sid}")
        if mqtt_client and mqtt_connected:
            emit('mqtt_status', {
                'status': 'conectado',
                'mensagem': f'Conectado ao broker MQTT {MQTT_BROKER}:{MQTT_PORT}'
            })
            if cache["dados"] and cache["timestamp"] and (time.time() - cache["timestamp"] < cache["ttl"]):
                emit('atualizacao_dados', cache["dados"])
        else:
            emit('mqtt_status', {
                'status': 'desconectado',
                'mensagem': 'Não conectado ao broker MQTT'
            })
    else:
        logger.warning(f"Tentativa de conexão WebSocket sem autenticação: {request.sid}")
        return False

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Cliente WebSocket desconectado: {request.sid}")

@socketio.on('solicitar_atualizacao')
def handle_solicitar_atualizacao():
    global mqtt_connected
    if mqtt_client and mqtt_connected and cache["dados"] and cache["timestamp"] and (time.time() - cache["timestamp"] < cache["ttl"]):
        emit('atualizacao_dados', cache["dados"])
        logger.info(f"Dados do cache enviados para cliente {request.sid}")
    else:
        logger.info(f"Nenhum dado recente disponível para {request.sid}")
        if not mqtt_connected:
            socketio.emit('mqtt_status', {'status': 'desconectado', 'mensagem': 'Não conectado ao broker MQTT'})

# === Inicialização do Servidor ===
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)