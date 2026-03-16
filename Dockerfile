FROM python:3.11-slim

WORKDIR /home

COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

COPY *.py ./
COPY rates.json ./
COPY templates/ ./templates/

RUN mkdir -p instance

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
