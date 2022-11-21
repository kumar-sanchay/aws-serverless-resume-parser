import os
import json
import uuid
import requests
import unittest
from unittest import mock
from lambda_code.upload_to_s3 import s3 as upload_s3, lambda_handler as upload_lambda_handler
from lambda_code.process_s3_events import s3 as process_s3, lambda_handler as process_lambda_handler


class TestUploadToS3Lambda(unittest.TestCase):

    def setUp(self):

        self.event = {
            'body': b'some fake file body'
        }

    @mock.patch.object(upload_s3, 'put_object', return_value=True)
    @mock.patch.dict(os.environ, {'UPLOAD_S3_NAME': 'TestS3'}, clear=True)
    def test_handler(self, client_stub):
        
        response = upload_lambda_handler(self.event, {})
        self.assertEqual(response['statusCode'], requests.codes.ALL_OK)
        self.assertEqual(json.loads(response['body'])['message'], 'File Uploaded')


class TestPracessS3EventHandler(unittest.TestCase):

    def setUp(self):

        # S3 event required dict values
        self.event = {
            'Records': [
                {
                    's3': {
                        'bucket': {
                            'name': 'some-bucket'
                        },
                        'object': {
                            'key': str(uuid.uuid4())
                        }
                    }
                },
            ]
        }

    @mock.patch.object(process_s3, 'Bucket')
    @mock.patch('lambda_code.process_s3_events.put_data_dynamodb')
    @mock.patch('builtins.open')
    @mock.patch.dict(os.environ, {'API_KEY': 'K', 'API_URL': 'u', 'DEBUG': '1'}, clear=True)
    def test_handler(self, s3_stub, dynamo_stub, open_stub):

        process_lambda_handler(self.event, {})

        dynamo_stub.assert_called_once()
        s3_stub.assert_called_once()