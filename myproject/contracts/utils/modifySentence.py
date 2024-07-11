import os

import requests
import json
import logging


def replaceStringFromPdf(api_key, file_url, search_strings, replace_strings):
    url = "https://api.pdf.co/v1/pdf/edit/replace-text"
    source_url = f'https://{os.getenv("AWS_STORAGE_BUCKET_NAME")}.s3.ap-northeast-2.amazonaws.com/{file_url}'

    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json"
    }

    parameters = {
        "name": "output.pdf",
        "password": "",
        "url": source_url,
        "searchStrings": search_strings,
        "replaceStrings": replace_strings,
        "replacementLimit": 0
    }
    # Logging configuration
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    response = requests.post(url, headers=headers, data=json.dumps(parameters))
    logger.debug("Response status code: %s", response.status_code)
    logger.debug("Response text: %s", response.text)

    response.raise_for_status()

    result_json = response.json()
    result_url = result_json.get('url')

    if result_url:
        download_response = requests.get(result_url)
        download_response.raise_for_status()
        return download_response.content
    else:
        raise Exception("Error: No URL found in the API response")