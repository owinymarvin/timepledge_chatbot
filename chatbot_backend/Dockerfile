FROM python:3.13-alpine AS builder
WORKDIR /chatbot_backend_image
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

FROM python:3.13-alpine AS final
WORKDIR /chatbot_backend_image
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /chatbot_backend_image/app.py .
RUN adduser -D dmarv
USER dmarv
CMD ["python", "app.py"]
