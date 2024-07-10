# 파이썬 3.11 이미지 사용
FROM python:3.11

# .pyc 파일 생성 억제 (컨테이너 환경에서 있으면 좋음)
ENV PYTHONDONTWRITEBYTECODE=1

# 실시간 로그 출력을 위해 버퍼 최소화
ENV PYTHONUNBUFFERED=1

# 컨테이너 내부 디렉토리를 백엔드로 설정
WORKDIR /backend

# 시스템 패키지 업데이트 및 설치
RUN apt-get update && apt-get install -y pkg-config

# requirements.txt 파일을 백엔드 디렉토리로 복사
COPY requirements.txt /backend/

# requirements.txt 파일을 이용해 필요한 패키지 설치
RUN pip install --upgrade pip && \
    pip install -r requirements.txt --no-cache-dir

# 소스코드를 컨테이너 내부 백엔드 디렉토리로 복사
COPY . /backend/

# Django 환경 변수를 설정합니다.
ENV DJANGO_SETTINGS_MODULE=myproject.settings

# Celery 명령어를 기본 명령어로 설정합니다.
CMD ["celery", "-A", "myproject", "worker", "--loglevel=info"]
