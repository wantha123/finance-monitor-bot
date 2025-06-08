
import os
import requests
from datetime import datetime

B2_BUCKET_ID = os.getenv("B2_BUCKET_ID")
B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APPLICATION_KEY = os.getenv("B2_APPLICATION_KEY")

def authorize_b2():
    response = requests.get(
        "https://api.backblazeb2.com/b2api/v2/b2_authorize_account",
        auth=(B2_KEY_ID, B2_APPLICATION_KEY)
    )
    response.raise_for_status()
    return response.json()

def upload_file_to_b2(file_path: str, file_name: str = None) -> str:
    auth_data = authorize_b2()
    upload_url_response = requests.post(
        f"{auth_data['apiUrl']}/b2api/v2/b2_get_upload_url",
        headers={"Authorization": auth_data["authorizationToken"]},
        json={"bucketId": B2_BUCKET_ID}
    )
    upload_url_response.raise_for_status()
    upload_info = upload_url_response.json()

    with open(file_path, 'rb') as f:
        file_data = f.read()

    if not file_name:
        file_name = os.path.basename(file_path)
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        file_name = f"{timestamp}_{file_name}"

    headers = {
        "Authorization": upload_info["authorizationToken"],
        "X-Bz-File-Name": file_name,
        "Content-Type": "application/octet-stream",
        "X-Bz-Content-Sha1": "do_not_verify"
    }

    upload_response = requests.post(
        upload_info["uploadUrl"],
        headers=headers,
        data=file_data
    )
    upload_response.raise_for_status()
    return upload_response.json().get("fileId")
