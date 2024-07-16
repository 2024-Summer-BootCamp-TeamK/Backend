from multiprocessing.pool import AsyncResult
from django.http import JsonResponse


def task_status(request, task_id):
    task = AsyncResult(task_id)

    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'result': task.result
        }
    elif task.state == 'FAILURE':
        response = {
            'state': task.state,
            'status': str(task.info),  # 예외 정보
        }
    else:
        response = {
            'state': task.state,
            'status': 'Processing...'
        }
    return JsonResponse(response)
