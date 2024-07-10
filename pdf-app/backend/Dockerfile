FROM python:3.12
WORKDIR /api
RUN apt-get update && apt-get install -y libhdf5-dev 
COPY . .
# NOTE: pymupdf 1.24.7 breaks in a container on Apple M-series
RUN pip install \
    fastapi==0.111.0 \
    uvicorn==0.30.1 \
    pymupdf==1.24.5 \ 
    scikit-learn==1.5.0 \
    openai==1.35.7 \
    sentence-transformers==3.0.1
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]