FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 16969

CMD ["gunicorn", "-b", "0.0.0.0:16969", "app:app"]
