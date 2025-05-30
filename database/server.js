const express = require("express");
const sqlite3 = require("sqlite3").verbose();
const { open } = require("sqlite");
const path = require("path");
const bodyParser = require("body-parser");
const cors = require("cors");
const bcrypt = require("bcrypt");

const app = express();
const PORT = 3000;

// Middleware
app.use(bodyParser.json());
app.use(cors());

// Middleware para logar requisições
app.use((req, res, next) => {
  const timestamp = new Date().toLocaleString('pt-BR');
  console.log(`[${timestamp}] Requisição: ${req.method} ${req.url}`);
  if (Object.keys(req.body).length > 0) {
    console.log(`[${timestamp}] Corpo: ${JSON.stringify(req.body)}`);
  }
  next();
});

let db;

async function initializeDatabase() {
  const timestamp = new Date().toLocaleString('pt-BR');
  console.log(`[${timestamp}] Inicializando banco de dados...`);
  db = await open({
    filename: path.join(__dirname, "data", "database.sqlite"), // Ajustado para /data
    driver: sqlite3.Database,
  });

  await db.exec(`
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      email TEXT NOT NULL UNIQUE,
      password_hash TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
  `);

  console.log(`[${timestamp}] Banco de dados inicializado com sucesso`);
}

// Rotas da API

// GET - Buscar usuário por ID
app.get("/api/users/:id", async (req, res) => {
  const timestamp = new Date().toLocaleString('pt-BR');
  const userId = req.params.id;
  try {
    console.log(`[${timestamp}] Buscando usuário com ID: ${userId}`);
    const user = await db.get("SELECT * FROM users WHERE id = ?", userId);
    if (!user) {
      console.log(`[${timestamp}] Usuário com ID ${userId} não encontrado`);
      res.status(404).json({ error: "Usuário não encontrado" });
      console.log(`[${timestamp}] Resposta enviada: 404 Not Found`);
      return;
    }
    console.log(`[${timestamp}] Usuário encontrado: ${user.email}`);
    res.json(user);
    console.log(`[${timestamp}] Resposta enviada: 200 OK`);
  } catch (error) {
    console.error(`[${timestamp}] Erro ao buscar usuário:`, error.message);
    res.status(500).json({ error: "Erro ao buscar usuário" });
    console.log(`[${timestamp}] Resposta enviada: 500 Internal Server Error`);
  }
});

// POST - Criar novo usuário
app.post("/api/users", async (req, res) => {
  const timestamp = new Date().toLocaleString('pt-BR');
  const { email, password } = req.body;

  if (!email || !password) {
    console.log(`[${timestamp}] Requisição inválida: Email ou senha ausentes`);
    res.status(400).json({ error: "Email e senha são obrigatórios" });
    console.log(`[${timestamp}] Resposta enviada: 400 Bad Request`);
    return;
  }

  try {
    console.log(`[${timestamp}] Verificando se email ${email} já existe...`);
    const existingUser = await db.get("SELECT id FROM users WHERE email = ?", email);
    if (existingUser) {
      console.log(`[${timestamp}] Email ${email} já cadastrado`);
      res.status(409).json({ error: "Email já cadastrado" });
      console.log(`[${timestamp}] Resposta enviada: 409 Conflict`);
      return;
    }

    console.log(`[${timestamp}] Hasheando senha para ${email}...`);
    const password_hash = await bcrypt.hash(password, 10);

    console.log(`[${timestamp}] Inserindo novo usuário: ${email}`);
    const result = await db.run(
      `INSERT INTO users (email, password_hash) VALUES (?, ?)`,
      [email, password_hash]
    );

    console.log(`[${timestamp}] Usuário criado com ID: ${result.lastID}`);
    const newUser = await db.get("SELECT * FROM users WHERE id = ?", result.lastID);
    res.status(201).json(newUser);
    console.log(`[${timestamp}] Resposta enviada: 201 Created`);
  } catch (error) {
    console.error(`[${timestamp}] Erro ao criar usuário:`, error.message);
    res.status(500).json({ error: "Erro ao criar usuário" });
    console.log(`[${timestamp}] Resposta enviada: 500 Internal Server Error`);
  }
});

// POST - Autenticar usuário
app.post("/api/login", async (req, res) => {
  const timestamp = new Date().toLocaleString('pt-BR');
  const { email, password } = req.body;

  if (!email || !password) {
    console.log(`[${timestamp}] Requisição inválida: Email ou senha ausentes`);
    res.status(400).json({ error: "Email e senha são obrigatórios" });
    console.log(`[${timestamp}] Resposta enviada: 400 Bad Request`);
    return;
  }

  try {
    console.log(`[${timestamp}] Buscando usuário com email: ${email}`);
    const user = await db.get("SELECT * FROM users WHERE email = ?", email);
    if (!user) {
      console.log(`[${timestamp}] Email ${email} não encontrado`);
      res.status(401).json({ error: "Email ou senha incorretos" });
      console.log(`[${timestamp}] Resposta enviada: 401 Unauthorized`);
      return;
    }

    console.log(`[${timestamp}] Verificando senha para ${email}...`);
    const isPasswordValid = await bcrypt.compare(password, user.password_hash);
    if (!isPasswordValid) {
      console.log(`[${timestamp}] Senha incorreta para ${email}`);
      res.status(401).json({ error: "Email ou senha incorretos" });
      console.log(`[${timestamp}] Resposta enviada: 401 Unauthorized`);
      return;
    }

    console.log(`[${timestamp}] Autenticação bem-sucedida para ${email}`);
    res.json({ id: user.id, email: user.email });
    console.log(`[${timestamp}] Resposta enviada: 200 OK`);
  } catch (error) {
    console.error(`[${timestamp}] Erro ao autenticar usuário:`, error.message);
    res.status(500).json({ error: "Erro ao autenticar" });
    console.log(`[${timestamp}] Resposta enviada: 500 Internal Server Error`);
  }
});

// DELETE - Remover usuário
app.delete("/api/users/:id", async (req, res) => {
  const timestamp = new Date().toLocaleString('pt-BR');
  const userId = req.params.id;

  try {
    console.log(`[${timestamp}] Buscando usuário com ID: ${userId}`);
    const user = await db.get("SELECT * FROM users WHERE id = ?", userId);
    if (!user) {
      console.log(`[${timestamp}] Usuário com ID ${userId} não encontrado`);
      res.status(404).json({ error: "Usuário não encontrado" });
      console.log(`[${timestamp}] Resposta enviada: 404 Not Found`);
      return;
    }

    console.log(`[${timestamp}] Removendo usuário ID ${userId}...`);
    await db.run("DELETE FROM users WHERE id = ?", userId);
    console.log(`[${timestamp}] Usuário ID ${userId} removido`);
    res.json({ message: "Usuário removido com sucesso" });
    console.log(`[${timestamp}] Resposta enviada: 200 OK`);
  } catch (error) {
    console.error(`[${timestamp}] Erro ao remover usuário:`, error.message);
    res.status(500).json({ error: "Erro ao remover usuário" });
    console.log(`[${timestamp}] Resposta enviada: 500 Internal Server Error`);
  }
});

// Inicializar o banco de dados e iniciar o servidor
initializeDatabase()
  .then(() => {
    const timestamp = new Date().toLocaleString('pt-BR');
    console.log(`[${timestamp}] Iniciando servidor na porta ${PORT}...`);
    app.listen(PORT, () => {
      console.log(`[${timestamp}] Servidor rodando na porta ${PORT}`);
    });
  })
  .catch((err) => {
    const timestamp = new Date().toLocaleString('pt-BR');
    console.error(`[${timestamp}] Erro ao inicializar o banco de dados:`, err.message);
    process.exit(1);
  });