import asyncio
import json
from utils.utils import upload_file_to_s3

"""upload images to s3 bucket and add s3 file path"""

BUCKET_NAME = 'cops-detector-pictures'

with open(f'test_data/joined_data.json', 'r') as source_file:
    source_json_data = json.load(source_file)


async def main():
    # limit concurrent access to 100
    semaphore = asyncio.Semaphore(100)

    tasks = []
    async with asyncio.TaskGroup() as tg:
        for item in source_json_data:
            try:
                task = tg.create_task(upload_file_to_s3(semaphore, BUCKET_NAME, item['img_path']))
                tasks.append(task)
            except KeyError:
                print('NO PATH')

    for task_result in tasks:
        bucket_name, remote_file_path = task_result.result()
        for item in source_json_data:
            try:
                if remote_file_path in item['img_path']:
                    item['s3_path'] = f'{bucket_name}/{remote_file_path}'
            except KeyError:
                pass
    with open(f'test_data/joined_data_s3.json', 'a+') as destination_file:
        json.dump(source_json_data, destination_file, ensure_ascii=False)


asyncio.run(main())
