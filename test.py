#!/usr/bin/env python3
import shutil
import time

import httpx

API_BASE_URL = 'http://localhost:8000'


models = httpx.get(f'{API_BASE_URL}/models/').json()
try:
    model = next(filter(lambda x: x['name'] == 'mnist', models))
except StopIteration:
    print('Creating model')
    shutil.make_archive('examples/mnist', 'zip', 'examples/mnist')
    with open('examples/mnist.zip', 'rb') as file:
        model = httpx.post(
            'http://localhost:8000/models/?name=mnist',
            files={'file': file},
        ).json()


print('Creating jobs')
files = [
    'examples/3.png',
    'examples/what.png',
]

job_ids = []
for file in files:
    with open(file, 'rb') as f:
        res = httpx.post('http://localhost:8000/files/', files={
            'file': f,
        })
        uploaded_path = res.json()['path']
        res = httpx.post('http://localhost:8000/jobs/', json={
            'model_id': model['id'],
            'argument_path': uploaded_path,
        })
        job_id = res.json()['id']
        job_ids.append(job_id)

for job_id in job_ids:
    status = httpx.get(f'http://localhost:8000/jobs/{job_id}').json()
    while status['status'] not in ['completed', 'failed']:
        print(f'Job {job_id} is {status["status"]}')
        time.sleep(1)
        status = httpx.get(f'http://localhost:8000/jobs/{job_id}').json()

    if status['status'] == 'failed':
        print(f'Job {job_id} failed')
        print(status['failed_log'])
    else:
        result_path = status['result_path']
        res = httpx.get(f'http://localhost:8000/files/{result_path}')
        print(res.text)
