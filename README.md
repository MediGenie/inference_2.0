# ML ops

## Install

```sh
poetry install
```


## Setup DB
```sh
export DATABASE_URL=postgresql://localhost/aiserving
alembic upgrade head
```


## Run

1. Web server
```sh
uvicorn ai_serving.main:app
```

2. Worker

Note that `--pool=solo` part is important as it creates child process to run AI model

```sh
celery -A ai_serving.tasks worker --loglevel=INFO --pool=solo --concurrency=4
```


## Test

To test, run `test.py`
It creates mnist model from examples, create two jobs using it
and prints the result after running it.
