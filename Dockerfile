FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY status_page_operator.py .

CMD ["kopf", "run", "status_page_operator.py"]