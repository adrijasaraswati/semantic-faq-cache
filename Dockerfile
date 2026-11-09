FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY faq_cache ./faq_cache
COPY data ./data
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && pip install --no-cache-dir .
ENV HF_HOME=/app/runtime/models
RUN useradd -m app && mkdir -p runtime && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["uvicorn", "faq_cache.api:app", "--host", "0.0.0.0", "--port", "8000"]
