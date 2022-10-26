import os
import json
import boto3
import logging
import requests
from functools import reduce
from boto3.dynamodb.conditions import Attr, Or
from botocore.exceptions import ClientError


logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

DEFALT_PAGE_SIZE = 5


def lambda_handler(event, context):
    
    try:
        params = event['multiValueQueryStringParameters']
        skills = params['skill'] if 'skill' in params else []
        page_size = int(params['page'][0]) if 'page' in params else DEFALT_PAGE_SIZE
        last_eval_key = dict(params['last_key'][0]) if 'last_key' in params else ''

        logger.info(f"Parameters: skills={skills}, page_size={page_size}, last_key={last_eval_key}")

        resp_data = get_resume_data(skills, page_size, last_eval_key)
        for data in resp_data['Items']:
            data['resume_key'] = get_resume_url(data['resume_key'])

        logger.info(resp_data)
        return {
            'statusCode': requests.codes.ALL_OK,
            'body': json.dumps({
                'items': resp_data['Items'],
                'last_key': resp_data['LastEvaluatedKey']
            })
        }
    except Exception as e:
        logger.exception(e)

    return {
        'statusCode': requests.codes.INTERNAL_SERVER_ERROR,
        'body': json.dumps({
            "message": "Something went wrong"
        })
    }


def get_resume_data(skills, page_size, last_eval_key):
    db_name = os.environ['STORE_TABLE_NAME']
    table = dynamodb.Table(db_name)

    conds = reduce(Or, ([Attr('skills').contains(s) for s in skills]))
    if last_eval_key:
        response = table.scan(
            FilterExpression=conds,
            Limit=page_size,
            ExclusiveStartKey=last_eval_key
        )
    else:
        response = table.scan(
                FilterExpression=conds,
                Limit=page_size,
            )
    return response


def get_resume_url(key, timeout=600):
    # Get presigned url
    bucket_name = os.environ['UPLOAD_S3_NAME']
    try:
        resp_url = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': key},
                                                    ExpiresIn=timeout)
        return resp_url
    except ClientError as e:
        logging.exception(e)
        return None                                    
