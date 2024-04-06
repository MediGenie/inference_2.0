from fastapi import Depends, FastAPI, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.datastructures import UploadFile as StarletteUploadFile

from . import models, object_storage, schemas, tasks
from .database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.mount('/static', StaticFiles(directory='mnist/build/static'), name='static')
templates = Jinja2Templates(directory='mnist/build')


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get('/')
def index(request: Request):
    # show index.html
    return templates.TemplateResponse('index.html', {'request': request})


@app.get('/models/', response_model=list[schemas.Model])
def list_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Model).offset(skip).limit(limit).all()


@app.get('/models/{model_id}', response_model=schemas.Model)
def read_model(model_id: int, db: Session = Depends(get_db)):
    db_model = db.query(models.Model).filter(models.Model.id == model_id).first()
    if db_model is None:
        raise HTTPException(status_code=404, detail='Model not found')
    return db_model


@app.post('/models/', response_model=schemas.Model)
def create_model(name: str, file: UploadFile, db: Session = Depends(get_db)):
    db_model = models.Model(name=name)
    db_model.module_path = ''
    db.add(db_model)
    db.commit()
    db.refresh(db_model)

    try:
        # Upload file to object storage
        object_path = f'models/{db_model.id}/{file.filename}'
        object_storage.put_object(
            object_path,
            file.file,
        )
        db_model.module_path = object_path
        db.commit()
    except Exception:
        db.delete(db_model)
        db.commit()
        raise

    return db_model


@app.post('/jobs/', response_model=schemas.Job)
def create_job(job: schemas.JobCreate, db: Session = Depends(get_db)):
    db_job = models.Job(model_id=job.dict()['model_id'])
    db.add(db_job)
    db.flush()

    try:
        for argument_info in job.dict()['argument_infos']:
            db_input_args = models.InputArgs(
                job_id=db_job.id,
                **argument_info
            )
            db.add(db_input_args)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    db.commit()
    tasks.preprocess.delay(db_job.id)
    db.refresh(db_job)
    return db_job


@app.get('/jobs/{job_id}', response_model=schemas.Job)
def read_job(job_id: str, db: Session = Depends(get_db)):
    db_job = db.query(models.Job).filter(models.Job.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail='Job not found')
    return db_job


@app.get('/jobs/', response_model=list[schemas.Job])
def read_jobs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Job).offset(skip).limit(limit).all()


@app.post('/uploads/')
def upload_values(value_list: list[UploadFile | str]) -> schemas.ArgsCreated:
    arg_infos = []

    for idx, value in enumerate(value_list):
        try:
            if isinstance(value, str):  # AI model input string (not url or path)
                arg_infos.append(schemas.ArgInfo(
                    value=value,
                    type=models.Type.TEXT,
                    index=idx
                ))
            elif isinstance(value, StarletteUploadFile):  # Only file
                object_path = f'uploads/{value.filename}'  # TODO: Need unique filename
                object_storage.put_object(
                    object_path,
                    value.file,
                )
                arg_infos.append(schemas.ArgInfo(
                    value=object_path,
                    type=models.Type.FILE,
                    index=idx
                ))
            else:
                raise HTTPException(status_code=400, detail=f'Unexpected value type: {type(value)}')
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return schemas.ArgsCreated(argument_infos=arg_infos)


@app.get('/results/{path:path}')
def get_result(path: str):
    res = object_storage.get_object(path)
    return Response(res.data, media_type='application/octet-stream')
