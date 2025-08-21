# 무신사 상품 리뷰 AI 분석 프로젝트

![Project Title](https://img.shields.io/badge/Project-MUSINSA%20Review%20Analysis-blue)
![Python](https://img.shields.io/badge/Python-3.8%2B-blueviolet)
![OpenAI](https://img.shields.io/badge/AI-OpenAI%20API-success)

## 1. 프로젝트 소개

본 프로젝트는 무신사(MUSINSA) 웹사이트의 상품 리뷰 데이터를 수집하고, 이를 AI 기술을 활용하여 분석하는 웹 대시보드입니다. 수많은 리뷰 데이터를 긍정/부정/중립으로 분류하고, 핵심 키워드를 추출하여 사용자가 상품의 특성을 한눈에 파악할 수 있도록 돕습니다.

## 2. 주요 기능

* **상품 리뷰 데이터 수집**: 무신사 웹사이트에서 특정 상품의 리뷰 데이터를 크롤링하여 수집합니다.
* **AI 기반 감정 분석**: 수집된 리뷰 텍스트를 OpenAI API를 활용하여 긍정, 부정, 중립으로 분류하고, 총평을 요약합니다.
* **핵심 키워드 추출**: 리뷰에서 자주 언급되는 핵심 키워드를 추출하여 상품의 주요 특징을 파악할 수 있도록 합니다.
* **시각화 대시보드**: 분석된 데이터를 사용자 친화적인 웹 대시보드 형태로 제공합니다.

## 3. 기술 스택

| 분류 | 기술 스택 | 설명 |
| :--- | :--- | :--- |
| **백엔드** | `Python` | 전체 프로젝트의 핵심 로직을 구현합니다. |
| | `OpenAI API` | 리뷰 텍스트의 감정 분석 및 요약에 사용됩니다. |
| | `pymysql` | 데이터베이스 연결 및 관리에 사용됩니다. |
| **프론트엔드** | `HTML`, `CSS`, `JavaScript` | 웹 대시보드를 구성합니다. |
| **데이터베이스**| `MySQL` | 크롤링한 상품 및 리뷰 데이터를 저장합니다. |

## 4. 설치 및 실행 방법

### 1) Prerequisites (사전 준비)
* Python 3.8 이상
* MySQL 데이터베이스
* OpenAI API Key

### 2) 환경 설정
1.  **프로젝트 클론**
    ```bash
    git clone [https://github.com/jeon99yu/MUSINSA_ReviewAnalysis.git](https://github.com/jeon99yu/MUSINSA_ReviewAnalysis.git)
    cd MUSINSA_ReviewAnalysis
    ```

2.  **가상 환경 설정**
    ```bash
    python -m venv venv
    source venv/bin/activate  # macOS/Linux
    venv\Scripts\activate     # Windows
    ```

3.  **의존성 패키지 설치**
    ```bash
    pip install -r requirements.txt
    ```

### 3) 데이터베이스 설정
* `db.py` 파일을 참고하여 MySQL 데이터베이스를 설정합니다.
* `config.py` 파일에 데이터베이스 접속 정보를 입력하거나, `.env` 파일을 생성하여 환경 변수를 설정합니다.
    ```
    # .env 파일 예시
    DB_HOST="localhost"
    DB_USER="root"
    DB_PASSWORD=""
    DB_NAME="reviewdb"
    OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
    ```

### 4) 실행
* **데이터 크롤링 및 DB 저장**
    ```bash
    python crawler.py
    ```
* **리뷰 분석 및 대시보드 실행**
    ```bash
    python app.py
    ```
    (이후 웹 브라우저에서 `http://localhost:5000`에 접속하여 대시보드 확인)
