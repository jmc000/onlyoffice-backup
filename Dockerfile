from python:3.14-slim

# run with rootless container runtime (podman)
# root in container == non-root user in  
USER 0

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/* .

ENTRYPOINT ["python", "main.py"]