#!/bin/sh

# set two worker for testing purposes. 큐 하나당 워커 하나면 됩니다.

celery -A backend worker --loglevel=info --concurrency=1 -n worker_1_@%h & # 워커 1번
celery -A backend worker --loglevel=info --concurrency=1 -n worker_2_@%h & # 워커 2번
celery -A backend worker --loglevel=info --concurrency=1 -n worker_3_@%h & # 워커 2번


celery -A backend flower --port=5555 --basic_auth=guest:guest --broker=$CELERY_BROKER_URL --broker_api=$CELERY_BROKER_API_URL #플라워 시작