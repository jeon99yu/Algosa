FROM python:3.11-slim

# 시스템 패키지
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# JDK(기본: 21) + 폰트
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-jdk-headless \
    fontconfig \
    libglib2.0-0 libgl1 \
 && rm -rf /var/lib/apt/lists/*

# 작업 디렉터리
COPY app.py      /app/app.py
COPY config.py   /app/config.py
COPY analyzer.py /app/analyzer.py       
COPY crawler.py  /app/crawler.py         
COPY db.py       /app/db.py

# 파이썬 의존성
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사 
COPY . /app

# 폰트 등록 
RUN mkdir -p /usr/local/share/fonts/truetype/local \
 && cp -r /app/font/* /usr/local/share/fonts/truetype/local/ 2>/dev/null || true \
 && fc-cache -fv

EXPOSE 8501

# 실행
CMD ["streamlit", "run", "/app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
# CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

