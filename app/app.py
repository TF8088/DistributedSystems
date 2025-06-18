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
MQTT_BROKER = os.getenv('MQTT_BROKER', 'cjsg.ddns.net')
MQTT_PORT = int(os.getenv('MQTT_PORT', 1883))
MQTT_TOPIC = os.getenv('MQTT_TOPIC', '/weather')
MQTT_USER = os.getenv('MQTT_USER', 'cd')
MQTT_PASS = os.getenv('MQTT_PASS', '1qaz\"WSX')

# Estado MQTT e cache
mqtt_connected = False
mqtt_client = mqtt.Client(client_id=f"mqtt_logger_{int(time.time())}")
cache = {
    "dados": None,
    "timestamp": 0,
    "ttl": 60
}

# === Callbacks MQTT ===
def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        logger.info(f"✅ Conectado ao broker MQTT: {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"📡 Inscrito no tópico: {MQTT_TOPIC}")
        socketio.emit('mqtt_status', {'status': 'conectado'})
    else:
        mqtt_connected = False
        logger.error(f"❌ Falha na conexão. Código de retorno: {rc}")
        socketio.emit('mqtt_status', {'status': 'erro', 'mensagem': f'Código {rc}'})

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode()
        try:
            data = json.loads(payload)
        except:
            data = payload
        cache["dados"] = data
        cache["timestamp"] = time.time()
        logger.info(f"📥 Mensagem recebida no tópico {msg.topic}: {payload}")
        socketio.emit('atualizacao_dados', data)
    except Exception as e:
        logger.error(f"Erro ao processar mensagem MQTT: {e}")

def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    logger.warning(f"🔌 Desconectado do broker. Código: {rc}")
    socketio.emit('mqtt_status', {'status': 'desconectado'})

# Inicializar conexão MQTT
def iniciar_mqtt():
    try:
        mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
        mqtt_client.on_connect = on_connect
        mqtt_client.on_message = on_message
        mqtt_client.on_disconnect = on_disconnect
        logger.info("🚀 A tentar conectar ao broker MQTT...")
        mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        mqtt_client.loop_start()
    except Exception as e:
        logger.error(f"Erro ao conectar com o broker MQTT: {e}")

# Autenticação

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'utilizador_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Rotas
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
            flash('Erro ao registrar utilizador', 'erro')
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
    nome_utilizador = session.get('nome_utilizador', 'utilizador')
    return render_template('index.html', nome_utilizador=nome_utilizador)

@app.route('/api/status-mqtt', methods=['GET'])
def status_mqtt():
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

# WebSocket Events
@socketio.on('connect')
def handle_connect():
    if 'utilizador_id' in session:
        logger.info(f"Cliente WebSocket conectado: {request.sid}")
        if mqtt_client and mqtt_connected:
            emit('mqtt_status', {
                'status': 'conectado',
                'mensagem': f'Conectado ao broker MQTT {MQTT_BROKER}:{MQTT_PORT}'
            })
            if cache["dados"] and (time.time() - cache["timestamp"] < cache["ttl"]):
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
    if mqtt_client and mqtt_connected and cache["dados"] and (time.time() - cache["timestamp"] < cache["ttl"]):
        emit('atualizacao_dados', cache["dados"])
        logger.info(f"Dados do cache enviados para cliente {request.sid}")
    else:
        logger.info(f"Nenhuns dados recentes disponíveis para {request.sid}")
        if not mqtt_connected:
            emit('mqtt_status', {'status': 'desconectado', 'mensagem': 'Não conectado ao broker MQTT'})

# Inicialização da conexão MQTT e do servidor Flask
if __name__ == '__main__':
    iniciar_mqtt()
    socketio.run(app, debug=False, host='0.0.0.0', port=5000)
