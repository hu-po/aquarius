FROM python:3.10-slim
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libv4l-dev \
    v4l-utils \
    udev \
    curl \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 appuser && \
    usermod -a -G video appuser
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY pyaquarius ./pyaquarius
COPY .env.example .env
RUN mkdir -p /app/data && \
    chown -R appuser:appuser /app
USER appuser
CMD ["uvicorn", "pyaquarius.main:app", "--host", "0.0.0.0", "--port", "8000"]