# webservice
A simple face-recognition service using Papillon

## Quick Start

Start the Celery Service..
```
celery -A webservice.celery worker -c 4
```

Start the web-service
```
python run.py
```

Run the test
```
./test/sh
```

## Pre-requisites

  * Installed Papillon SDK
  * Python packages Celery, Flask, SqlAlchemy, SQLite




