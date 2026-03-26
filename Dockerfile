FROM python:3.12-slim AS base

Workdir /app

Copy requirements.txt .
Run pip install --no-cache-dir -r requirements.txt

COPY . .

ENV FLASK_ENV=production
ENV ENTORNO=produccion

EXPOSE 5000

CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
