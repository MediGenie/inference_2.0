import os
import threading
import time

import numpy as np

from celery import Celery
from celery.utils.log import get_task_logger

from . import models
from .database import SessionLocal
from .model_worker import ModelWorker

EncodedInputs = bytes


REDIS_URL = os.getenv('REDIS_URL')

app = Celery('tasks', backend='rpc://', broker=REDIS_URL)

model_workers = {}  # model_id -> ModelWorker

logger = get_task_logger(__name__)


def load_model(model_id: int):
    global model_workers

    if model_id in model_workers:
        # Model already loaded
        return

    db = SessionLocal()
    print(f'Setting up model {model_id}')
    model = db.query(models.Model).filter(models.Model.id == model_id).one()
    model_workers[model_id] = ModelWorker(model)


def progress_updater(job_id):
    db = SessionLocal()
    job = db.query(models.Job).filter(models.Job.id == job_id).one()
    update_interval = 3

    while job.status not in (models.JobStatus.PENDING, models.JobStatus.FAILED, models.JobStatus.COMPLETED):
        try:
            updated_job_progress: str | None = model_workers[job.model_id].update_progress()
            if updated_job_progress:
                job = db.query(models.Job).filter(models.Job.id == job_id).one()
                job.progress = updated_job_progress
                db.add(job)
                db.commit()
                db.refresh(job)

            time.sleep(update_interval)

            job = db.query(models.Job).filter(models.Job.id == job_id).one()
        except Exception as e:
            print(f"progres_updater failed: {e}")
            break

    if job.status == models.JobStatus.COMPLETED:  # For last status update
        job = db.query(models.Job).filter(models.Job.id == job_id).one()
        job.progress = updated_job_progress
        db.add(job)
        db.commit()
        db.refresh(job)


@app.task
def preprocess(job_id: int):
    db = SessionLocal()
    print(f'Preprocessing job {job_id}')
    job = db.query(models.Job).filter(models.Job.id == job_id).one()

    job.status = models.JobStatus.PREPROCESSING
    db.add(job)
    db.commit()

    try:
        # Ensure model is loaded
        load_model(job.model_id)

        input_args: list[models.InputArgs] = (
            db.query(models.InputArgs)
            .filter(models.InputArgs.job_id == job_id)
            .order_by(models.InputArgs.index).all()
        )

        launch_progress_updater(job_id)

        inputs = model_workers[job.model_id].preprocess(input_args)
    except Exception as e:
        job.status = models.JobStatus.FAILED
        job.failed_log = str(e)
        db.add(job)
        db.commit()
        raise e

    job.status = models.JobStatus.PREPROCESSED
    db.add(job)
    db.commit()

    inference.delay(job_id, inputs)


@app.task
def inference(job_id: int, inputs: EncodedInputs):
    db = SessionLocal()
    print(f'Inferencing job {job_id}')
    job = db.query(models.Job).filter(models.Job.id == job_id).one()

    job.status = models.JobStatus.INFERENCING
    db.add(job)
    db.commit()

    try:
        # Ensure model is loaded
        load_model(job.model_id)

        outputs = model_workers[job.model_id].inference(inputs)
    except Exception as e:
        job.status = models.JobStatus.FAILED
        job.failed_log = str(e)
        db.add(job)
        db.commit()
        raise e

    job.status = models.JobStatus.INFERENCED
    db.add(job)
    db.commit()

    postprocess.delay(job_id, outputs)


@app.task
def postprocess(job_id: int, outputs: list[np.ndarray]):
    db = SessionLocal()
    print(f'Postprocessing job {job_id}')
    job = db.query(models.Job).filter(models.Job.id == job_id).one()

    job.status = models.JobStatus.POSTPROCESSING
    db.add(job)
    db.commit()

    try:
        # Ensure model is loaded
        load_model(job.model_id)

        result_path = model_workers[job.model_id].postprocess(job, outputs)
    except Exception as e:
        job.status = models.JobStatus.FAILED
        job.failed_log = str(e)
        db.add(job)
        db.commit()
        raise e

    job.status = models.JobStatus.COMPLETED
    job.result_path = result_path
    db.add(job)
    db.commit()


def launch_progress_updater(job_id: int):
    t = threading.Thread(target=progress_updater, args=(job_id,), name='progress_updater')

    t.start()
