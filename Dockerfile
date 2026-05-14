FROM --platform=linux/amd64 python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV ENTROPY_TEMPLATE_PATH=/app/entropy-template
ENV PYTHONUNBUFFERED=1
# TEMP: diagnose smaller-vault regression after Sonnet 4.6 switch.
# Writes per-chunk wiki artifacts to s3://.../jobs/{id}/wiki_debug/.
# Remove this line once root cause is identified.
ENV ENTROPY_WIKI_DEBUG=1
CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
