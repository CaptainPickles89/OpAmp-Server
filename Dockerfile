FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

# Copy runtime code and generated stubs
COPY server.py opamp_pb2.py anyvalue_pb2.py requirements.txt ./

# Install runtime dependencies only
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "server.py"]
