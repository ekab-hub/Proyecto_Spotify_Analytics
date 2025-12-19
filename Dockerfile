FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY src /app/src
COPY assets /app/assets
COPY datos/procesados /app/datos/procesados

EXPOSE 8501

CMD ["streamlit", "run", "src/analitica_spotify/dashboard.py", "--server.address=0.0.0.0", "--server.port=8501"]

