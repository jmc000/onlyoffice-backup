import requests
import json
import yaml
import os
import logging
import argparse
import math

from dotenv import load_dotenv
from requests.adapters import HTTPAdapter, Retry
from datetime import datetime, timezone
from contextlib import contextmanager
from pydantic import ValidationError

from models import (
    CreateUploadSessionReturnedResponse,
    GetMyDocumentsFolderIdReturnedResponse,
    UploadChunkReturnedResponse,
    UploadReturnedResponse,
)


class OnlyOfficeUploader:
    def __init__(self, api_key: str, docspace_url: str, health_check_url: str):
        self._docspace_url = docspace_url
        self._health_check_url = health_check_url
        self._api_key = api_key
        self._headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        self._supported_files = {".docx", ".xlsx", ".pptx"}
        self._small_file_limit = 10 * 1024 * 1024
        self._chunk_upload_size = self._small_file_limit - 1
        self._retries = Retry(total=5, backoff_factor=1)
        self._session = self._create_session()
        self._folder_id = None

    @property
    def folder_id(self) -> str:
        if self._folder_id is None:
            self._folder_id = self._get_mydocuments_folder_id()
        if self._folder_id is None:
            raise RuntimeError("Could not retrieve folder ID — check logs for details")
        return self._folder_id

    @contextmanager
    def _fail_on_error(self):
        try:
            yield
        except (requests.exceptions.RequestException, OSError, RuntimeError, AttributeError, ValidationError) as e:
            logging.error(f"Error: {e}")
            self.health_check_fail()
    
    def _get_mydocuments_folder_id(self):
        with self._fail_on_error():
            response = self._session.get(
                f"{self._docspace_url}/api/2.0/files/@my",
                headers=self._headers
            )
            response.raise_for_status()
            parsed_response = GetMyDocumentsFolderIdReturnedResponse.model_validate(response.json())
            folder_id = parsed_response.response.current.id
            return folder_id

    def _create_session(self) -> requests.Session:
        s = requests.Session()
        s.mount('https://', HTTPAdapter(max_retries=self._retries))
        return s
    
    def health_check_start(self):
        with self._fail_on_error():
            response = self._session.get(
                f"{self._health_check_url}/start"
            )
            response.raise_for_status()
            logging.info(f"Notified /start to healthchecks.io")
            return

    def health_check_fail(self):
        try:
            response = self._session.get(
                f"{self._health_check_url}/fail"
            )
            response.raise_for_status()
            logging.info(f"Notified /fail to healthchecks.io")
            return

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to ping healthchecks.io /fail endpoint with HTTP error: {e}")
            return

    def health_check_success(self):
        with self._fail_on_error():
            response = self._session.get(
                f"{self._health_check_url}"
            )
            response.raise_for_status()
            logging.info(f"Notified success to healthchecks.io")
            return
    
    def upload_files(self, files: list[str]):
        for f in files:
            self._upload_file(f)

    def _iter_supported_files(self, d: str):
        for x in os.listdir(d):
            absolute_path = os.path.join(d, x)
            if os.path.isfile(absolute_path) and os.path.splitext(x)[1] in self._supported_files:
                yield absolute_path

    def upload_dir(self, dirs: list[str]):
        for d in dirs:
            for path in self._iter_supported_files(d):
                self._upload_file(path)

    def _upload_file(self, file: str):
        with self._fail_on_error():
            file_size_bytes = os.path.getsize(file)
            if file_size_bytes > self._small_file_limit:
                self._upload_large_file(file,file_size_bytes)
                return

            with open(file, 'rb') as f:
                http_response = self._session.post(
                    f"{self._docspace_url}/api/2.0/files/{self.folder_id}/upload",
                    headers=self._headers,
                    files={'file': f},
                    data={'CreateNewIfExist': True}
                )
                http_response.raise_for_status()
                result = http_response.json()
                parsed_result = UploadReturnedResponse.model_validate(result)

                logging.info(f"File: {parsed_result.response[0].title} uploaded successfully!")
                logging.info(f"\tVersion: {parsed_result.response[0].version}")

    def _upload_large_file(self, file: str, file_size_bytes: int):
        logging.info("Uploading large file in chunks")
        logging.info(f"File: {file} - Size: {file_size_bytes}")

        dt = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'

        file_name = os.path.basename(file)
        payload = {
            'fileName': file_name,
            'fileSize': file_size_bytes,
            'createOn': dt,
            'encrypted': False,
            'createNewIfExist': False
        }

        with self._fail_on_error():
            #1. Start upload session
            response = self._session.post(
                f"{self._docspace_url}/api/2.0/files/{self.folder_id}/upload/create_session",
                headers={**self._headers, 'Content-Type': 'application/json'},
                json=payload
            )
            response.raise_for_status()
            parsed_response = CreateUploadSessionReturnedResponse.model_validate(response.json())
            upload_location = parsed_response.response.data.location

            # 2. upload chunks
            with open(file, 'rb') as f:
                total_chunks = math.ceil(file_size_bytes / self._chunk_upload_size)

                for chunk_id in range(1, total_chunks + 1):
                    chunk_data = f.read(self._chunk_upload_size)
                    if not chunk_data:
                        raise RuntimeError(f"Chunk {chunk_id} data is empty.")

                    files = {
                        'file': (file, chunk_data, 'application/octet-stream')
                    }

                    # Upload chunk
                    logging.info(f"Uploading chunk {chunk_id}/{total_chunks}")
                    response = self._session.post(
                        upload_location,
                        headers=self._headers,
                        files=files
                    )
                    response.raise_for_status()
                    response_data = response.json()
                    parsed_response = UploadChunkReturnedResponse.model_validate(response_data)
                    request_success = parsed_response.success

                    # Status code can be 200 but success = failed
                    if not request_success:
                        raise requests.exceptions.RequestException(
                            f"Error uploading chunk {chunk_id}:\n{json.dumps(parsed_response.model_dump(), indent=2)}"
                        )

                version = parsed_response.data.file.version
                logging.info(f"File: {file} uploaded in chunks successfully!")
                logging.info(f"\tVersion: {version}")

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("API_KEY")
    docspace_url = os.getenv("DOCSPACE_URL")
    health_check_url = os.getenv("HEALTH_CHECK_URL")
    if not api_key or not docspace_url:
        raise EnvironmentError("API_KEY and DOCSPACE_URL must be set")

    logging.basicConfig(filename='output.log', level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()

    logging.info(f"Loading config file: {args.config}")
    try:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        logging.error(f"Config file not found: {args.config}")
        raise
    except yaml.YAMLError as e:
        logging.error(f"Failed to parse config file: {args.config} with error: {e}")
        raise
    except OSError as e:
        logging.error(f"Failed to open config file: {args.config} with error: {e}")
        raise

    if not config:
        logging.warning("Config file is empty, nothing to do")
    else:
        files = config.get("files", [])
        dirs = config.get("dirs", [])

        if not files and not dirs:
            logging.warning("No files or dirs specified in config, nothing to do")
        else:
            only_office = OnlyOfficeUploader(api_key, docspace_url, health_check_url)
            logging.info("Starting script")
            only_office.health_check_start()
            if files:
                logging.info(f"files: {files}")
                only_office.upload_files(files)
            if dirs:
                logging.info(f"directories: {dirs}")
                only_office.upload_dir(dirs)
            only_office.health_check_success()
