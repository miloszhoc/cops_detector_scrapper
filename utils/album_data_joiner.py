import os
import json
import re

TEST_DATA_PATH = 'test_data/group_photos/'
files = os.listdir(TEST_DATA_PATH)
files.remove('.DS_Store')
files.remove('pictures')

json_f = []

for i, file in enumerate(files):
    with open(f'test_data/group_photos/{file}', 'r') as source_file:
        print(source_file.name)
        file_data = source_file.read().split('-------------')
        json_data = []
        for line in file_data:
            record = {}
            match_description = re.search(r"DESCRIPTION:(.*?)IMG_URL:", line, re.DOTALL)  # match also new line
            if match_description:
                description_text = match_description.group(1).strip()
                record['description'] = description_text
            else:
                print("No match found")

            match_url = re.search(r"IMG_URL:\s*(.*)", line)
            if match_url:
                img_url = match_url.group(1).strip()
                record['img_url'] = img_url
            else:
                print("No match found")
            match_img_path = re.search(r"IMG_PATH:\s*(.*)", line)
            if match_img_path:
                img_path = match_img_path.group(1).strip()
                record['img_path'] = img_path
            else:
                print("No match found")
            json_data.append(record)
            # print(json_data)
        json_f.extend(json_data)

with open(f'test_data/joined_data.json', 'w+') as destination_file:
    json.dump(json_f, destination_file, ensure_ascii=False)

