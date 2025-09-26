FROM otel/opentelemetry-collector-contrib:latest
COPY config.yaml /etc/otelcol-contrib/config.yaml

EXPOSE 4317 4318 8098 8099
CMD ["--config=/etc/otelcol-contrib/config.yaml"]