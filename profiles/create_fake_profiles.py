import json
import random


with open('./profiles/origin_data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

profiles = []

for i in range(30):
    name = random.choice(data['male_names'])
    description = random.choice(data['male_descriptions'])
    profile = {
        "city": random.choice(data['cities']),
        "age": random.randint(18, 30),
        "gender": 'Мужчина',
        'preferences': 'Женщины',
        "name": name,
        "description": description,
    }
    profiles.append(profile)

for i in range(30):
    name = random.choice(data['female_names'])
    description = random.choice(data['female_descriptions'])
    profile = {
        "city": random.choice(data['cities']),
        "age": random.randint(18, 30),
        "gender": 'Женщина',
        'preferences': 'Мужчины',
        "name": name,
        "description": description,
    }
    profiles.append(profile)

with open('./profiles/profiles.json', 'w', encoding='utf-8') as file:
    json.dump(profiles, file, ensure_ascii=False, indent=2)
