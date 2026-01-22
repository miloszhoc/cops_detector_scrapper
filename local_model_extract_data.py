import json
from shutil import copy
import time
from gpt4all import GPT4All

copy('test_data/joined_data.json', 'test_data/joined_data_final.json')

# model = GPT4All("Meta-Llama-3-8B-Instruct.Q4_0.gguf", device='cuda')  # downloads / loads a 4.66GB LLM
model = GPT4All("Nous-Hermes-2-Mistral-7B-DPO.Q4_0.gguf", device='cuda')

with (open('test_data/joined_data.json', 'r',
           encoding='UTF-8') as f_source, open('test_data/joined_data_final.json', 'r',
                                               encoding='UTF-8') as f_dest):
    source_data = json.load(f_source)
    dest_data = json.load(f_dest)

    start_time = int(time.time())
    print(start_time)
    for source, destination in zip(source_data, dest_data):
        with model.chat_session():
            # print(source['description'])
            resp = model.generate(f"""
            {source['description']}
        
            From the above information presented in Polish, extract the Polish name of the province and city, make and model of car, current Polish vehicle registration number consisting of numbers and letters. If there are, previous registration numbers and Polish numbers of roads on which the vehicle moves. save the results in json format with the structure:
            {{voivodeship : province name (string),
            city: city (string),
            car_info: car make and model (string),
            current_licence_plate_number: current Polish vehicle registration number consisting of numbers and letters (string)
            old_license_plates: previous registration numbers (list),
            road_numbers: Polish numbers of roads on which the vehicle moves (list),
            }}
            if data is missing, leave blank. Return only the json structure and nothing else.
            """, max_tokens=1024)
            # .format(content=source['description'])
            print(resp)
            # destination['extracted_data'] = json.dumps(resp)
end_time = int(time.time())

print(f'execution time {end_time - start_time}sec.')
