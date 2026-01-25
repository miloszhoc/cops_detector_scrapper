import os
import pathlib

BUCKET_NAME = os.environ['S3_BUCKET_NAME']
PROJECT_ROOT_FOLDER = pathlib.Path(__file__).parent.parent.absolute()
TEST_DATA_ROOT_FOLDER = f'{PROJECT_ROOT_FOLDER}/test_data'
COOKIES_PROMPT = False