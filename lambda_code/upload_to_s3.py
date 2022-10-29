"""
    upload_to_s3 will be used as lambda backend for uploading resume through api gateway.
"""
import os
import base64
import boto3
import json
import requests
import uuid


s3 = boto3.client('s3')

def lambda_handler(event, context):
    # lambda for storing resumes in S3 bucket for further processing
    s3_name = os.environ['UPLOAD_S3_NAME']
    if s3_name and 'body' in event:

        get_file_content = event['body']
        decoded_content = base64.b64decode(get_file_content)
        filename = str(uuid.uuid4())  # generate unique filename
        upload = s3.put_object(Bucket=s3_name, Key=filename, Body=decoded_content)

        if upload:
            return {
                'statusCode': requests.codes.ALL_OK,
                'body': json.dumps({
                    "message": "File Uploaded"
                })
            }

    return {
        'statusCode': requests.codes.INTERNAL_SERVER_ERROR,
        'body': json.dumps({
            "message": "Something went wrong"
        })
    }
