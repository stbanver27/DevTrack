FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar proyecto
COPY . .

# Puerto dinámico que Railway asigna
EXPOSE 8000

# Seed + arranque
CMD python seed.py && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
