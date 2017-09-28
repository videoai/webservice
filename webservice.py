from flask import Flask, request, jsonify
from celery import Celery
from celery.signals import worker_process_init
from flask_sqlalchemy import SQLAlchemy
import shortuuid
from werkzeug import secure_filename
import os
import Papillon as papillon
import shutil

STORAGE_PATH = '/tmp'

def make_celery(app):
    celery = Celery(app.import_name, backend=app.config['CELERY_RESULT_BACKEND'],
                    broker=app.config['CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
    celery.Task = ContextTask
    return celery


app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = make_celery(app)

# Set-up the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


class DescriptionMixin(object):
    @property
    def papillon_description(self):
        description = papillon.PDescription()
        ps = papillon.PString(self.description)
        description.FromBase64(ps)
        return description

    @papillon_description.setter
    def papillon_description(self, value):
        self.description = value.ToBase64()

class Description(db.Model, DescriptionMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=False)
    description = db.Column(db.Binary)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Id {} Name i{}>'.format(self.id, self.name)


@celery.task()
def do_enrol(name, job_dir, image_path):

   
    # Load the image
    image = papillon.PImage()
    if image.Load(image_path).Failed():
        print 'Failed to load image'
        return

    # Detect the faces in the image
    detection_list = papillon.PDetectionList()
    if detector.Detect(papillon.PFrame(image), detection_list).Failed():
        print 'Failed to detect faces'
        return
   
    # For each face enrol it
    print 'We have found {} faces in {}'.format(detection_list.Size(), image_path)
    for i in range(0, detection_list.Size()):

        detection = detection_list.Get(i)

        description = papillon.PDescription()
        if describer.Describe(detection, name, papillon.PGuid.CreateUniqueId(), description).Failed():
            print 'Failed to generate description'
            return
        print 'Generated description for {}'.format(name)

        # Lets store it in the database
        d = Description(name)
        d.papillon_description = description
        db.session.add(d)
    
    # commit all changes to database
    db.session.commit()

    # tidy-up
    shutil.rmtree(job_dir)

    return 


@celery.task()
def do_search(job_dir, image_path):
  
    # Lets make the watchlist
    # You would not really do this in a production application - you should have a persistent watch list
    watchlist = papillon.PWatchlist()
    descriptions = Description.query.all()
    for description in descriptions:
        watchlist.Add(description.papillon_description)
    print 'Made a watchlist with {} entries'.format(watchlist.Size())

    # Load the image
    image = papillon.PImage()
    if image.Load(image_path).Failed():
        print 'Failed to load image'
        return

    # Detect the faces in the image
    detection_list = papillon.PDetectionList()
    if detector.Detect(papillon.PFrame(image), detection_list).Failed():
        print 'Failed to detect faces'
        return
  
    # For each face enrol it
    print 'We have found {} faces in {}'.format(detection_list.Size(), image_path)
    for i in range(0, detection_list.Size()):

        detection = detection_list.Get(i)

        description = papillon.PDescription()
        if describer.Describe(detection, 'Unknown', papillon.PGuid.CreateUniqueId(), description).Failed():
            print 'Failed to generate description'
            return

        results = papillon.PIdentifyResults() 
        if watchlist.Search(description,
                            compare,
                            results,
                            1,
                            0.5).Failed():
            print 'Failed to search watchlist'
            return
        
        for i in range(0, results.Size()):
            identification_result = results.Get(i)
            print identification_result.ToString()
    
    # tidy-up
    shutil.rmtree(job_dir)
    return 


class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/')
def index():
    return "Welcome to the small Papillon Web-Service example!"

@app.route('/enrol', methods=['POST'])
def enrol():

    if request.method == 'POST':
        # get the image
        if 'image' not in request.files:
            raise InvalidUsage('Need an image file for this routine!')
        image = request.files['image']
        # get the name 
        name = ''
        if 'name' in request.form:
            name = request.form['name']

        # make a job and save data to a temp folder
        job_id = str(shortuuid.uuid())
        job_folder = '{}/{}'.format(STORAGE_PATH, job_id)
        os.mkdir(job_folder)
        image_path = '{}/{}'.format(job_folder, secure_filename(image.filename))
        image.save(image_path)
        # pass it off to celery to process asynchronously
        celery_task = do_enrol.apply_async(args=[name, job_folder, image_path])
        
        # lets give some data back to the user
        result = {
            'job_id':job_id,
            'message':'Enrol job for {} queued for processing'.format(name)
        }
        response = jsonify(result)
        return response

@app.route('/search', methods=['POST'])
def search():

    if request.method == 'POST':
        # get the image
        if 'image' not in request.files:
            raise InvalidUsage('Need an image file for this routine!')
        image = request.files['image']

        # make a job and save data to a temp folder
        job_id = str(shortuuid.uuid())
        job_folder = '{}/{}'.format(STORAGE_PATH, job_id)
        os.mkdir(job_folder)
        image_path = '{}/{}'.format(job_folder, secure_filename(image.filename))
        image.save(image_path)
        # pass it off to celery to process asynchronously
        celery_task = do_search.apply_async(args=[job_folder, image_path])
        
        # lets give some data back to the user
        result = {
            'job_id':job_id,
            'message':'Search job queued for processing'
        }
        response = jsonify(result)
        return response
        
                                
# Initialise worker
@worker_process_init.connect
def process_init(sender=None, conf=None, **kwargs):

    print "Initialising Papillon"
    # Initialise the Papillon SDK.  Note, you will need to make sure we can find libs and plugin directory
    papillon.PLog_OpenConsoleLogger(papillon.PLog.E_LEVEL_INFO)
    papillon.PLog_SetFormat("console", "[date] (sev) [file:line]: msg")
    papillon.PLog_OpenFileLogger("file", "/tmp/papillon.txt", papillon.PLog.E_LEVEL_DEBUG)
    papillon.PLog_SetFormat("file", "[date] (sev) [file:line]: msg")
    papillon.PapillonSDK.Initialise().OrDie()

    # Load in a detector for this process
    global detector
    detector = papillon.PDetector()
    papillon.PDetector.Create("FaceDetector2", papillon.PProperties(), detector)
    detector.SetMinDetectionSize(80)
    detector.Set(papillon.PDetector.C_PARAM_BOOL_LOCALISER.c_str(), True)

    # Load in a comparer for this process
    global compare
    compare = papillon.PComparer()
    papillon.PComparer.Create(compare)

    # Load in a describer for this process
    global describer
    describer = papillon.PDescriber()
    properties = papillon.PProperties()
    properties.Set('gpuId', int(0))
    papillon.PDescriber.Create("DescriberDnn", properties, describer)