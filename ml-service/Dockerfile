FROM python:3.11-slim

WORKDIR /app

# CPU 전용 torch (CUDA 빌드 회피로 이미지 경량화)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# e5 임베딩 모델을 이미지에 미리 받아둠 (콜드스타트 단축). 리랭커는 배포 시 RERANK=0이라 생략.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-base')"

COPY app.py .

ENV RERANK=0
# Cloud Run은 PORT 환경변수를 주입한다.
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}
