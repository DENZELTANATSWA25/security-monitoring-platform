FROM python:3.11-slim

WORKDIR /app

# install dependencies first (better caching)
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# copy app code
COPY . .

# ensure uvicorn is available via python module (important fix)
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]