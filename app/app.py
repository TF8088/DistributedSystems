from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import json
import threading
import time
import secrets
from datetime import datetime
from functools import wraps
import logging
import os
import glob
import requests

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Inicialização do Flask e SocketIO
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
socketio = SocketIO(app, cors_allowed_origins="*")

# Configurações da API Express
API_BASE_URL = os.getenv('NODE_SERVER_URL', 'http://localhost:3000')

# Configurações MQTT padrão
MQTT_CONFIG_DIR = "mqtt_configs"
MQTT_DEFAULT_CONFIG = os.path.join(MQTT_CONFIG_DIR, "default.json")

# Criar pasta para configurações, se não existir
if not os.path.exists(MQTT_CONFIG_DIR):
    os.makedirs(MQTT_CONFIG_DIR)

# Criar default.json com configurações iniciais, se não existir
def initialize_default_config():
    default_config = {
        "broker": "cjsg.ddns.net",
        "port": 1883,
        "topic": "/weather",
        "username": "",
        "password": "",
        "client_id": f"weather_client_{secrets.token_hex(4)}"
    }
    if not os.path.exists(MQTT_DEFAULT_CONFIG):
        try:
            with open(MQTT_DEFAULT_CONFIG, 'w') as f:
                json.dump(default_config, f, indent=4)
            logger.info(f"Arquivo {MQTT_DEFAULT_CONFIG} criado com configurações padrão")
        except Exception as e:
            logger.error(f"Erro ao criar {MQTT_DEFAULT_CONFIG}: {e}")
    return default_config

# Carregar configurações MQTT do arquivo padrão
def load_mqtt_credentials():
    try:
        if os.path.exists(MQTT_DEFAULT_CONFIG):
            with open(MQTT_DEFAULT_CONFIG, 'r') as f:
                config = json.load(f)
                logger.info(f"Configurações carregadas de {MQTT_DEFAULT_CONFIG}")
                return (
                    config.get('broker', 'cjsg.ddns.net'),
                    config.get('port', 1883),
                    config.get('topic', '/weather'),
                    config.get('username', ''),
                    config.get('password', ''),
                    config.get('client_id', f"weather_client_{secrets.token_hex(4)}")
                )
        else:
            logger.warning(f"Arquivo {MQTT_DEFAULT_CONFIG} não encontrado, usando configurações padrão")
            return initialize_default_config().values()
    except Exception as e:
        logger.error(f"Erro ao carregar configurações MQTT de {MQTT_DEFAULT_CONFIG}: {e}")
        return initialize_default_config().values()

MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID = load_mqtt_credentials()

# Cache para dados meteorológicos
cache = {
    "dados": None,
    "timestamp": None,
    "ttl": 60  # Tempo de vida do cache em segundos
}

# Cliente MQTT global e estado da conexão
mqtt_client = None
mqtt_connected = False

# === Funções de Autenticação ===
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'utilizador_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# === Funções MQTT ===
def on_connect(client, userdata, flags, rc, properties=None):
    global mqtt_connected
    if rc == 0:
        logger.info(f"Conectado ao broker MQTT")
        client.subscribe(MQTT_TOPIC, qos=1)
        logger.info(f"Inscrito no tópico {MQTT_TOPIC}")
        mqtt_connected = True
        socketio.emit('mqtt_status', {'status': 'conectado', 'mensagem': f'Conectado ao broker MQTT'})
    else:
        logger.error(f"Falha na conexão ao broker MQTT: código {rc}")
        mqtt_connected = False
        socketio.emit('mqtt_status', {'status': 'erro', 'mensagem': f'Falha na conexão ao broker MQTT: código {rc}'})

def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode('utf-8')
        dados = json.loads(payload)
        cache["dados"] = dados
        cache["timestamp"] = time.time()
        socketio.emit('atualizacao_dados', dados)
        logger.info(f"Dados recebidos: {payload}")
    except Exception as e:
        logger.error(f"Erro ao processar mensagem: {e}")

def on_disconnect(client, userdata, rc, properties=None, reason=None):
    global mqtt_connected
    logger.warning(f"Desconectado do broker MQTT: código {rc}")
    mqtt_connected = False
    socketio.emit('mqtt_status', {'status': 'desconectado', 'mensagem': f'Desconectado do broker MQTT: código {rc}'})

def iniciar_cliente_mqtt(broker, port, topic, username, password, client_id):
    global mqtt_client, MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID, mqtt_connected
    if mqtt_client:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    
    MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID = (
        broker, port, topic, username, password, client_id or f"weather_client_{secrets.token_hex(4)}"
    )
    
    mqtt_client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311, callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect

    if username and password:
        mqtt_client.username_pw_set(username, password)
        logger.info(f"Autenticação configurada com usuário: {username}")

    mqtt_client.enable_logger(logger)
    mqtt_client.reconnect_delay_set(min_delay=1, max_delay=120)

    def reconnect_loop():
        while True:
            try:
                if not mqtt_connected:
                    logger.info(f"Tentando conectar ao broker {MQTT_BROKER}:{MQTT_PORT}")
                    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
                    mqtt_client.loop_start()
                    logger.info("Cliente MQTT iniciado")
                    break
                time.sleep(10)
            except Exception as e:
                logger.error(f"Erro ao conectar ao broker: {e}")
                mqtt_connected = False
                socketio.emit('mqtt_status', {'status': 'erro', 'mensagem': f'Erro ao conectar: {str(e)}'})
                time.sleep(5)

    threading.Thread(target=reconnect_loop, daemon=True).start()
    return True, "Conexão iniciada com sucesso"

# Iniciar MQTT em uma thread separada
threading.Thread(target=lambda: iniciar_cliente_mqtt(
    MQTT_BROKER, MQTT_PORT, MQTT_TOPIC, MQTT_USERNAME, MQTT_PASSWORD, MQTT_CLIENT_ID
), daemon=True).start()

# === Funções Auxiliares ===
def compare_configs(new_config, existing_config):
    """Compara duas configurações MQTT, ignorando client_id se não especificado."""
    return (
        new_config['broker'] == existing_config.get('broker', '') and
        new_config['port'] == existing_config.get('port', 1883) and
        new_config['topic'] == existing_config.get('topic', '') and
        new_config['username'] == existing_config.get('username', '') and
        new_config['password'] == existing_config.get('password', '') and
        new_config['client_id'] == existing_config.get('client_id', new_config['client_id'])
    )

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
            flash('Erro ao registrar usuário', 'erro')
    except requests.RequestException as e:
        logger.error(f"Erro ao chamar API: {e}")
        flash('Erro ao conectar com a API', 'erro')
    return redirect(url_for('register'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    nome_utilizador = session.get('nome_utilizador', 'Usuário')
    return render_template('index.html', nome_utilizador=nome_utilizador)

@app.route('/api/status-mqtt', methods=['GET'])
@login_required
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

@app.route('/api/configurar-mqtt', methods=['POST'])
@login_required
def configurar_mqtt():
    data = request.get_json()
    broker = data.get('broker')
    port = data.get('port')
    topic = data.get('topic')
    username = data.get('username', '')
    password = data.get('password', '')
    client_id = data.get('client_id')
    filename = data.get('filename')
    
    if not broker or not port or not topic:
        return jsonify({"error": "Broker, porta, tópico são obrigatórios"}), 400
    
    try:
        port = int(port)
        if port < 1 or port > 65535:
            raise ValueError("Porta inválida")
    except ValueError:
        return jsonify({"error": "Porta deve ser um número entre 1 e 65535"}), 400
    
    config = {
        "broker": broker,
        "port": port,
        "topic": topic,
        "username": username,
        "password": password,
        "client_id": client_id or f"weather_client_{secrets.token_hex(4)}"
    }
    
    # Verificar se é uma configuração existente
    if filename:
        config_path = os.path.join(MQTT_CONFIG_DIR, filename)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    existing_config = json.load(f)
                if compare_configs(config, existing_config):
                    # Configuração não alterada, apenas reconectar
                    logger.info(f"Configuração {filename} não alterada, aplicando...")
                    success, message = iniciar_cliente_mqtt(broker, port, topic, username, password, client_id)
                    if success:
                        return jsonify({"message": message}), 200
                    else:
                        return jsonify({"error": message}), 500
                else:
                    # Configuração alterada, atualizar arquivo existente
                    try:
                        with open(config_path, 'w') as f:
                            json.dump(config, f, indent=4)
                        logger.info(f"Configuração {filename} atualizada")
                        # Reconectar com a configuração atualizada
                        success, message = iniciar_cliente_mqtt(broker, port, topic, username, password, client_id)
                        if success:
                            return jsonify({"message": message}), 200
                        else:
                            return jsonify({"error": message}), 500
                    except Exception as e:
                        logger.error(f"Erro ao atualizar configuração {filename}: {e}")
                        return jsonify({"error": f"Erro ao atualizar configuração {filename}"}), 500
            except Exception as e:
                logger.error(f"Erro ao ler configuração {filename}: {e}")
                return jsonify({"error": f"Erro ao ler configuração {filename}"}), 500
        else:
            return jsonify({"error": f"Arquivo {filename} não encontrado"}), 404
    
    # Criar nova configuração apenas se nenhuma configuração existente foi selecionada
    try:
        config_name = f"config_{int(time.time())}.json"
        config_path = os.path.join(MQTT_CONFIG_DIR, config_name)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        logger.info(f"Nova configuração salva em {config_path}")
        # Reconectar com a nova configuração
        success, message = iniciar_cliente_mqtt(broker, port, topic, username, password, client_id)
        if success:
            return jsonify({"message": message}), 200
        else:
            return jsonify({"error": message}), 500
    except Exception as e:
        logger.error(f"Erro ao salvar nova configuração MQTT: {e}")
        return jsonify({"error": "Erro ao salvar nova configuração"}), 500

@app.route('/api/listar-configs-mqtt', methods=['GET'])
@login_required
def listar_configs_mqtt():
    try:
        configs = []
        # Incluir default.json
        if os.path.exists(MQTT_DEFAULT_CONFIG):
            with open(MQTT_DEFAULT_CONFIG, 'r') as f:
                config = json.load(f)
                configs.append({
                    "filename": "default.json",
                    "broker": config.get('broker', ''),
                    "port": config.get('port', 1883),
                    "topic": config.get('topic', ''),
                    "username": config.get('username', ''),
                    "password": config.get('password', ''),
                    "client_id": config.get('client_id', '')
                })
        # Incluir configs adicionais
        config_files = glob.glob(os.path.join(MQTT_CONFIG_DIR, "config_*.json"))
        for config_file in config_files:
            with open(config_file, 'r') as f:
                config = json.load(f)
                configs.append({
                    "filename": os.path.basename(config_file),
                    "broker": config.get('broker', ''),
                    "port": config.get('port', 1883),
                    "topic": config.get('topic', ''),
                    "username": config.get('username', ''),
                    "password": config.get('password', ''),
                    "client_id": config.get('client_id', '')
                })
        logger.info(f"Listadas {len(configs)} configurações MQTT")
        return jsonify(configs), 200
    except Exception as e:
        logger.error(f"Erro ao listar configurações MQTT: {e}")
        return jsonify({"error": "Erro ao listar configurações"}), 500

# === Eventos SocketIO ===
@socketio.on('connect')
def handle_connect():
    global mqtt_connected
    if 'utilizador_id' in session:
        logger.info(f"Cliente WebSocket conectado: {request.sid}")
        # Enviar status inicial do MQTT ao conectar
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
        logger.info(f"Nenhum dado recente disponível, aguardando mensagem MQTT para {request.sid}")
        if not mqtt_connected:
            socketio.emit('mqtt_status', {'status': 'desconectado', 'mensagem': 'Não conectado ao broker MQTT'})

# === Inicialização do Servidor ===
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)