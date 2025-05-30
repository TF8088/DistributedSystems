# Usar uma imagem base Python 3.9 slim
FROM python:3.9-slim

# Definir diretório de trabalho
WORKDIR /app

# Copiar requirements.txt e instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o código
COPY app.py .
COPY templates/ templates/
COPY mqtt_configs/ mqtt_configs/

# Expor a porta 5000
EXPOSE 5000

# Iniciar com gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]