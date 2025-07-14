FROM python:3.11-slim

# Instala ffmpeg y otras dependencias
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Carpeta de trabajo
WORKDIR /app

# Copiar archivos de la app
COPY . .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer puerto esperado por Fly.io
EXPOSE 8080

# Ejecutar Flask en puerto 8080
CMD ["python", "backend.py"]
