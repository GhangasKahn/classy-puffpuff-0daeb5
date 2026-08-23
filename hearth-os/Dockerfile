FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home --uid 10001 hearth \
    && mkdir -p /app/data \
    && chown -R hearth:hearth /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=hearth:hearth . .

USER hearth
ENV PYTHONPATH=/app
ENV DATABASE_URL=sqlite:////app/data/hearth.db
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health')"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
