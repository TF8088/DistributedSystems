# Estação Meteorológica com Flask, MQTT e SocketIO

Uma aplicação web para monitoramento de dados meteorológicos em tempo real, utilizando Flask, MQTT para coleta de dados, SocketIO para atualizações em tempo real e autenticação via API externa.

## Requisitos

- Python 3.8 ou superior
- pip para instalação de pacotes
- Node.js (para a API de autenticação externa)
- Broker MQTT (ex.: Mosquitto)
- Navegador web moderno

## Instalação

1. Clone o repositório ou baixe os arquivos.
2. Crie e ative um ambiente virtual (opcional, mas recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
3. Instale as dependências:
```bash
pip install -r requirements.txt
```
4. Configure a API de autenticação externa (rodando em `http://localhost:3000`).
5. Configure o broker MQTT com as credenciais corretas (endereço, porta, usuário e senha).

## Configuração

As configurações principais estão no arquivo Python:

- **API de Autenticação**:
  - `API_BASE_URL`: Endereço da API de autenticação (padrão: `http://localhost:3000`).
- **MQTT**:
  - `MQTT_BROKER`: Endereço do broker MQTT (padrão: `cjsg.ddns.net`).
  - `MQTT_PORT`: Porta do broker (padrão: `1883`).
  - `MQTT_TOPIC`: Tópico para assinatura (padrão: `/weather`).
  - `MQTT_USERNAME` e `MQTT_PASSWORD`: Credenciais do broker.
- **Cache**:
  - `ttl`: Tempo de vida do cache em segundos (padrão: `60`).

Certifique-se de que o broker MQTT e a API de autenticação estejam acessíveis antes de iniciar a aplicação.

## Executando a Aplicação

Para iniciar o servidor Flask com SocketIO:

```bash
python app.py
```

O servidor será iniciado na porta `5000` por padrão e estará acessível em `http://localhost:5000`. Para alterar a porta ou host, modifique a chamada `socketio.run` no final do arquivo.

## Estrutura da Aplicação

### Rotas Flask
- **/login** (GET/POST): Página de login e autenticação via API externa.
- **/register** (GET): Página de registro.
- **/registrar** (POST): Endpoint para registro de novos usuários.
- **/logout** (GET): Finaliza a sessão do usuário.
- **/** (GET): Página principal (requer autenticação).
- **/api/dados-meteorologicos** (GET): Retorna dados meteorológicos em cache ou dados de exemplo.

### Eventos SocketIO
- **connect**: Estabelece conexão WebSocket (requer autenticação).
- **disconnect**: Registra desconexão de um cliente.
- **solicitar_atualizacao**: Solicita envio de dados meteorológicos em cache.
- **atualizacao_dados**: Emite atualizações de dados para clientes conectados.

### Funcionalidades MQTT
- Conexão ao broker MQTT para coleta de dados em tempo real.
- Assinatura no tópico `/weather` para receber atualizações.
- Cache de dados com tempo de vida configurável.

## Endpoints da API Externa

A aplicação depende de uma API externa para autenticação (não incluída neste código). Os endpoints utilizados são:

- **POST /api/login**: Autentica um usuário.
  - Corpo da requisição:
    ```json
    {
      "email": "usuario@exemplo.com",
      "password": "senha"
    }
    ```
- **POST /api/users**: Registra um novo usuário.
  - Corpo da requisição:
    ```json
    {
      "email": "usuario@exemplo.com",
      "password": "senha"
    }
    ```

## Testando a Aplicação

1. Inicie a API de autenticação externa (se necessário).
2. Inicie o broker MQTT.
3. Execute o servidor Flask (`python app.py`).
4. Acesse `http://localhost:5000` em um navegador.
5. Registre ou faça login para acessar a página principal.
6. Verifique as atualizações de dados meteorológicos em tempo real.

## Estrutura de Dados Meteorológicos

Os dados meteorológicos seguem o formato:

```json
{
  "temperatura": 25.5,
  "umidade": 65,
  "pressao": 1013,
  "velocidade_vento": 12,
  "direcao_vento": "NE",
  "condicao": "Parcialmente nublado",
  "timestamp": "DD/MM/YYYY HH:MM:SS"
}
```

## Logging

A aplicação utiliza logging para monitoramento:
- Nível: INFO (pode ser ajustado em `logging.basicConfig`).
- Formato: `%(asctime)s - %(levelname)s - %(message)s`.
- Mensagens incluem conexão/desconexão MQTT, erros de API e eventos de WebSocket.

## Notas Adicionais

- A aplicação usa um cache para reduzir chamadas desnecessárias e melhorar a performance.
- Dados de exemplo são retornados se o cache estiver vazio ou expirado.
- A autenticação é obrigatória para acessar a página principal e os dados meteorológicos.
- O cliente MQTT roda em uma thread separada para não bloquear o servidor Flask.
- As templates HTML (`login.html`, `register.html`, `index.html`) devem estar na pasta `templates`.

## Dependências

As dependências estão listadas em `requirements.txt`. As principais são:

- `flask`: Framework web.
- `flask-socketio`: Suporte a WebSocket.
- `paho-mqtt`: Cliente MQTT.
- `requests`: Chamadas HTTP para a API externa.

Instale com:
```bash
pip install flask flask-socketio paho-mqtt requests
```

## Solução de Problemas

- **Erro de conexão MQTT**: Verifique o endereço, porta e credenciais do broker.
- **Erro de API**: Confirme que a API externa está rodando em `http://localhost:3000`.
- **WebSocket não conecta**: Certifique-se de que o usuário está autenticado.
- **Dados não atualizam**: Verifique o tópico MQTT e a conectividade do broker.