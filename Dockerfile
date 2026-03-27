FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/app

# Copy runtime code, generated stubs, and server package
COPY server.py opamp_pb2.py anyvalue_pb2.py requirements.txt ./
COPY opamp_server/ ./opamp_server/

# Install runtime dependencies only
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["python", "server.py"]
