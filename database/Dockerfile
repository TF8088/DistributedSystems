# Usar uma imagem base Node.js 18
FROM node:18

# Definir diretório de trabalho
WORKDIR /app

# Copiar package.json e instalar dependências
COPY package.json .
RUN npm install

# Copiar o código
COPY server.js .

# Criar diretório para banco de dados
RUN mkdir -p /app/data

# Expor a porta 3000
EXPOSE 3000

# Iniciar o servidor
CMD ["node", "server.js"]