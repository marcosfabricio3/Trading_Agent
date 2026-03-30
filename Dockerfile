FROM python:3.12-slim

# Evitar que Python genere archivos .pyc y habilitar modo sin búfer
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=.

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema necesarias (gcc, libssl para Telethon)
RUN apt-get update && apt-get install -y \
    gcc \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias e instalarlas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto de la FastAPI
EXPOSE 8000

# Comando para arrancar el bot (Engine + API)
CMD ["python", "-m", "app.main"]
