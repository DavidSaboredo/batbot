# Usar imagen base con más herramientas preinstaladas
FROM python:3.11-bullseye

# Instalar dependencias del sistema necesarias
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libnacl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Actualizar pip y herramientas
RUN pip install --upgrade pip setuptools wheel

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias paso a paso para mejor debugging
RUN pip install --no-cache-dir discord.py==2.3.2
RUN pip install --no-cache-dir Flask==2.3.3  
RUN pip install --no-cache-dir aiohttp==3.9.1
RUN pip install --no-cache-dir PyNaCl==1.5.0

# Copiar código
COPY . .

# Exponer puerto para Render
EXPOSE 8080

# Comando de inicio
CMD ["python", "main.py"]
