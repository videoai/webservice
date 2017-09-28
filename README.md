# Papillon FaceRec Web Service 

A very simple face-recognition service using Papillon, Flask, Celery, SqlAlchemy and SQLite.

## Quick Start

Start the Celery Service, limiting the number of workers.
```
celery -A webservice.celery worker -c 4
```

Start the web-service which runs the API
```
python run.py
```

Run the test
```
./test.sh
```

## Pre-requisites

  * Installed Papillon SDK
  * Python packages Celery, Flask, SqlAlchemy, SQLite, redis




