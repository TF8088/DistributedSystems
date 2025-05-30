# Projeto de Monitoramento Meteorológico

Um sistema completo para monitoramento de dados meteorológicos em tempo real, composto por dois servidores: uma aplicação web Flask com MQTT e SocketIO para exibição de dados e uma API Node.js com SQLite para autenticação de usuários.

## Visão Geral

O projeto é dividido em dois componentes principais:
1. **Estação Meteorológica (Flask)**: Uma aplicação web que coleta dados meteorológicos via MQTT, exibe-os em tempo real com SocketIO e gerencia sessões de usuário autenticadas por uma API externa.
2. **API de Usuários (Node.js)**: Uma API RESTful para gerenciamento de usuários, incluindo autenticação e registro, utilizando SQLite como banco de dados.

## Requisitos

- Python 3.8 ou superior
- Node.js (versão 14 ou superior)
- pip e npm (ou yarn) para instalação de dependências
- Broker MQTT (ex.: Mosquitto)
- Navegador web moderno

## Instalação

1. Clone o repositório ou baixe os arquivos.
2. Navegue até o diretório do projeto.

### Para o Servidor Flask
3. Crie e ative um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
4. Instale as dependências do Flask:
```bash
pip install -r flask_server/requirements.txt
```

### Para a API Node.js
5. Navegue até o diretório da API Node.js (ex.: `node_api`):
```bash
cd node_api
```
6. Instale as dependências:
```bash
npm install
```

## Configuração

### Servidor Flask
As configurações estão no arquivo `flask_server/app.py`:
- **API de Autenticação**: `API_BASE_URL` (padrão: `http://localhost:3000`).
- **MQTT**:
  - `MQTT_BROKER`: Endereço do broker (padrão: `cjsg.ddns.net`).
  - `MQTT_PORT`: Porta (padrão: `1883`).
  - `MQTT_TOPIC`: Tópico (padrão: `/weather`).
  - `MQTT_USERNAME` e `MQTT_PASSWORD`: Credenciais do broker.
- **Cache**: `ttl` (padrão: `60` segundos).

### API Node.js
As configurações estão no arquivo `node_api/server.js`:
- **Porta**: Definida pela variável de ambiente `PORT` (padrão: `3000`).
- **Banco de Dados**: SQLite, criado automaticamente em `node_api/database.sqlite`.

Certifique-se de que o broker MQTT esteja acessível e configurado corretamente.

## Executando o Projeto

Para iniciar ambos os servidores simultaneamente, execute o script principal:

```bash
python main.py
```

- O servidor Flask será iniciado em `http://localhost:5000`.
- A API Node.js será iniciada em `http://localhost:3000`.

## Estrutura do Projeto

```
project_root/
├── flask_server/
│   ├── app.py              # Código do servidor Flask
│   ├── templates/          # Arquivos HTML (login.html, register.html, index.html)
│   └── requirements.txt    # Dependências Python
├── node_api/
│   ├── server.js           # Código da API Node.js
│   ├── test-api.js         # Script de teste da API
│   ├── database.sqlite     # Banco de dados SQLite (criado automaticamente)
│   └── package.json        # Dependências Node.js
├── main.py                 # Script principal para iniciar ambos os servidores
└── README.md               # Documentação do projeto
```

## Testando o Projeto

1. Inicie o broker MQTT.
2. Execute `python main.py` para iniciar ambos os servidores.
3. Acesse `http://localhost:5000` em um navegador.
4. Registre-se ou faça login para visualizar os dados meteorológicos.
5. Para testar a API Node.js isoladamente:
```bash
cd node_api
node test-api.js
```

## Dependências

### Flask
- `flask`: Framework web.
- `flask-socketio`: Suporte a WebSocket.
- `paho-mqtt`: Cliente MQTT.
- `requests`: Chamadas HTTP.

### Node.js
- `express`: Framework web.
- `sqlite3`: Banco de dados SQLite.
- Outras dependências listadas em `node_api/package.json`.

## Solução de Problemas

- **Erro de conexão MQTT**: Verifique as credenciais e a conectividade do broker.
- **Erro de API**: Confirme que a API Node.js está rodando em `http://localhost:3000`.
- **Servidores não iniciam**: Verifique se as portas `3000` e `5000` estão livres.
- **WebSocket não conecta**: Certifique-se de que o usuário está autenticado.

## Notas Adicionais

- O `main.py` gerencia a inicialização de ambos os servidores e encerra os processos adequadamente.
- A API Node.js deve estar configurada para aceitar requisições de `http://localhost:5000` (CORS).
- As templates HTML do Flask devem estar na pasta `flask_server/templates`.