# Papillon FaceRec Web Service 

A very simple face-recognition service using Papillon, Flask, Celery, SqlAlchemy and SQLite.
This service has been developped for Linux. Python scripts must be adapted to run under Windows.

## Quick Start

### Pre-requisites

Install Papillon SDK from Digital Barriers

Install the required Python packages:
```
pip install redis
pip install Celery
pip install Flask
pip install SQLAlchemy
pip install Flask_SQLAlchemy
pip install shortuuid
```

### Set environment variables
Set the following environment variables (if not already set):
```
export PYTHONPATH=/opt/Papillon/lib
export PAPILLON_INSTALL_DIR=/opt/Papillon
export LD_LIBRARY_PATH=/opt/Papillon/lib
```

Start the Celery Service, limiting the number of workers:
```
celery -A webservice.celery worker -c 4
```

Start the web-service which runs the API:
```
python run.py
```

Run the test
```
./test.sh
```
