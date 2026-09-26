FROM python:3.11-slim

WORKDIR /app

# install dependencies files first so Docker can cache dependency installation.
COPY requirements.txt requirements-dev.txt ./


# Install application dependencies plus development/testing tools
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-dev.txt

# copy the application source code into the image
COPY . .

# Start the FastAPI application.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]