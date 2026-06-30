FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data_json logs

ENTRYPOINT ["python", "main.py"]
CMD ["--keyword", "esp32", "--max-pages", "1"]
