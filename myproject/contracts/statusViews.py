from celery.result import AsyncResult
from rest_framework.response import Response

from rest_framework.views import APIView

class TaskStatusView(APIView):

    def get(self, request, task_id):
        task = AsyncResult(task_id)
        response = {
            'task_id': task_id,
            'status': task.state,
            'result': task.result if task.state == 'SUCCESS' else None
        }
        return Response(response)
