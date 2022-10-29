"""
    This lambda function will be used for returning resumes based on query params.
    Resume will be returned as a pre-signed link, valid till timeout.
"""
import os
import json
import boto3
import logging
import requests
from decimal import Decimal
from functools import reduce
from boto3.dynamodb.conditions import Attr, Or
from botocore.exceptions import ClientError


logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3 = boto3.resource('s3')
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

DEFALT_PAGE_SIZE = 5


class ResumeStoreSchema:
    def __init__(self) -> None:
        self.id = 'id'
        self.fullname = 'fullname'
        self.email = 'email'
        self.skills = 'skills'
        self.resume_key = 'resume_key'
        self.exp = 'exp'
        self.cr_timestamp = 'cr_timestamp'


class ParameterSchema:
    def __init__(self) -> None:
        self.id = 'id'
        self.page = 'page'
        self.skill = 'skill'
        self.last_key = 'last_key'
        self.cr_timestamp = 'cr_timestamp'


class DecimalEncoder(json.JSONEncoder):
    """
        Encode decimal values as string in json.
    """
    def default(self, ob):
        if isinstance(ob, Decimal):
            return str(ob)
        return super(DecimalEncoder, self).default(ob)


class InCompleteLastKey(Exception):
    """
        InCompleteLastKey will be raised
        when any params is missed for lastkey
    """

class MissingRequiredParams(Exception):
    """
        Raised when required request params
        is missing.
    """


def lambda_handler(event, context):
    
    try:
        param_schema = ParameterSchema()
        store_schema = ResumeStoreSchema()

        key_attr = [param_schema.last_key, param_schema.cr_timestamp]
        required_params = [param_schema.skill, param_schema.page]
        params = event['multiValueQueryStringParameters']

        if not params or not all(key in params for key in required_params):
            raise MissingRequiredParams

        skills = params[param_schema.skill] if param_schema.skill in params else []
        page_size = int(params[param_schema.page][0]) if param_schema.page in params else DEFALT_PAGE_SIZE
        last_eval_key = {}

        if (param_schema.last_key in params or param_schema.cr_timestamp in params): 
            if not all(key in params for key in key_attr):
                # Both key attr should be present as params
                raise InCompleteLastKey
            else:
                last_eval_key[store_schema.id] = params[param_schema.last_key][0]
                last_eval_key[store_schema.cr_timestamp] = params[param_schema.cr_timestamp][0]

        logger.info(f"Parameters: skills={skills}, page_size={page_size}, last_key={last_eval_key}")

        resp_data = get_resume_data(skills, page_size, last_eval_key)
        for data in resp_data['Items']:
            data[store_schema.resume_key] = get_resume_url(data[store_schema.resume_key])

        last_key = resp_data['LastEvaluatedKey'] if 'LastEvaluatedKey' in resp_data else {param_schema.id: resp_data['Items'][-1][store_schema.id],
                                                                                          param_schema.cr_timestamp: resp_data['Items'][-1][store_schema.cr_timestamp]}

        return {
            'statusCode': requests.codes.ALL_OK,
            'body': json.dumps({
                'items': resp_data['Items'],
                'last_key': last_key
            }, cls=DecimalEncoder)
        }

    except (MissingRequiredParams, InCompleteLastKey) as e:
        logger.exception(e)

        return {
        'statusCode': requests.codes.BAD_REQUEST,
        'body': json.dumps({
            "message": "Missing Parameters"
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
    store_schema = ResumeStoreSchema()
    skills = list(map(lambda s: s.lower(), skills))
    # creating condition with Or based on skill
    conds = reduce(Or, ([Attr(store_schema.skills).contains(s) for s in skills]))
    if last_eval_key:
        response = table.scan(
            FilterExpression=conds,
            Limit=page_size,
            ExclusiveStartKey=last_eval_key
        )
    else:
        response = table.scan(
                FilterExpression=conds,
                Limit=page_size
            )
    return response


def get_resume_url(key, timeout=600):
    # Get presigned url
    # This resume url will fail after timeout secs
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
