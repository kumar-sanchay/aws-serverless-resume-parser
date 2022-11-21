"""
    This lambda function will be called by S3 bucket on file creation event.
    It will extract datapoints from the resume and will put into dynamodb table.
"""
import os
import boto3
import datetime
import logging
import json
import tempfile
import uuid
import urllib
import requests

# Setup logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb')


class Item:
    def __init__(self, name, email, skills, exp, resume_key):
        self.id = str(uuid.uuid4())
        self.fullname = name
        self.email = email
        self.skills = list(map(lambda s: s.lower(), skills))  # store in lower case
        self.resume_key = resume_key
        self.exp = exp
        self.cr_timestamp = str(datetime.datetime.now())

    def get_obj(self):
        return self.__dict__

def lambda_handler(event, context):

    try:
        logger.info(event)
        s3_bucket_name = event['Records'][0]['s3']['bucket']['name']
        key = str(urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8'))

        # download s3 file in tmp dir for further processing
        with tempfile.TemporaryFile(dir='/tmp') as temp_resume:
            s3.Bucket(s3_bucket_name).download_file(key, os.path.join('/tmp', str(temp_resume.name)))
            with open(os.path.join('/tmp', str(temp_resume.name)), 'rb') as resume:
                resume_data = resume.read()
                data_points = get_resume_data_points(resume_data)
                if data_points:
                    item = Item(data_points['name'], data_points['email'], data_points['skills'], 0, key)
                    put_data_dynamodb(item)
                    logger.info('Successfully added item.')

    except Exception as e:
        logger.exception(e)


def get_resume_data_points(data):
    api_url = os.environ['API_URL']
    api_key = os.environ['API_KEY']
    debug = bool(int(os.environ['DEBUG']))

    if debug:
        # Debug will not make any api calls
        return get_test_data_points()

    headers = {'Content-Type': 'application/octet-stream', 'apikey': api_key}
    req = requests.post(api_url, headers=headers, data=data)

    if req.status_code == requests.codes.ALL_OK:
        return json.loads(req.text)

    logger.warning(f'Third party api call failed with status={req.status_code}, msg={req.text}')
    return None


def put_data_dynamodb(item):
    """
        Insert extracted resume data points in dynamo db.
    """
    table_name = os.environ['STORE_TABLE_NAME']
    db_table = dynamodb.Table(table_name)
    db_table.put_item(
        Item=item.get_obj()
    )

def get_test_data_points():
    data = {
        "name": "abc",
        "email": "abc@gmail.com",
        "phone": "+91 0000000000",
        "skills": [
            "Php",
            "Java",
            "Computer science",
            "C",
            "Json",
            "Python"
        ]
    }
    return data