                                                                                                                                  # API de Usuários com Node.js e SQLite

Uma API simples para gerenciamento de usuários utilizando Node.js, Express e SQLite.

## Requisitos

- Node.js (versão 14 ou superior)
- npm ou yarn

## Instalação

1. Clone o repositório ou baixe os arquivos
2. Instale as dependências:

```bash
npm install
```

## Executando a API

Para iniciar o servidor:

```bash
npm start
```

Para iniciar em modo de desenvolvimento (com reinício automático):

```bash
npm run dev
```

O servidor será iniciado na porta 3000 por padrão. Você pode alterar a porta definindo a variável de ambiente `PORT`.

## Endpoints da API

### Listar todos os usuários
```
GET /api/users
```

### Buscar usuário por ID
```
GET /api/users/:id
```

### Criar novo usuário
```
POST /api/users
```

Corpo da requisição:
```json
{
  "email": "usuario@exemplo.com",
  "password_hash": "hash_da_senha",
  "verification_code": "1234",
  "is_verified": false,
  "isAdmin": false,
  "profile_picture": "/caminho/para/imagem.jpg"
}
```

### Atualizar usuário
```
PUT /api/users/:id
```

Corpo da requisição (todos os campos são opcionais):
```json
{
  "email": "novo_email@exemplo.com",
  "password_hash": "novo_hash_da_senha",
  "verification_code": "5678",
  "is_verified": true,
  "isAdmin": true,
  "profile_picture": "/novo/caminho/para/imagem.jpg"
}
```

### Remover usuário
```
DELETE /api/users/:id
```

## Testando a API

Um script de teste está incluído para verificar o funcionamento da API. Para executá-lo:

```bash
node test-api.js
```

Certifique-se de que o servidor esteja em execução antes de executar o script de teste.

## Estrutura do Banco de Dados

A API utiliza SQLite com a seguinte estrutura de tabela:

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  email TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  verification_code TEXT NOT NULL,
  is_verified INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  isAdmin INTEGER DEFAULT 0,
  profile_picture TEXT DEFAULT '/static/imgs/default-profile.png'
)
```

O banco de dados é criado automaticamente no arquivo `database.sqlite` quando o servidor é iniciado pela primeira vez.
