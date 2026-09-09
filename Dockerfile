FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY mystictools ./mystictools
RUN pip install --no-cache-dir .

USER 65532:65532
EXPOSE 9108
ENTRYPOINT ["mysticexporter"]
CMD ["--root", "/mystic", "--bind", "0.0.0.0", "--port", "9108"]
