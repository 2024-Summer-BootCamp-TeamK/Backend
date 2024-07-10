from celery import shared_task

@shared_task()
def pdf_to_s3(document, file_name, file):
  document.pdfUrl.save(file_name, file)
