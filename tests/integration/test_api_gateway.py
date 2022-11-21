import os
from unittest import TestCase
from urllib import response

import boto3
import requests

"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test. 
"""


class TestApiGateway(TestCase):

    @classmethod
    def get_stack_name(cls) -> str:
        stack_name = os.environ['AWS_SAM_STACK_NAME']
        if not stack_name:
            raise Exception(
                "Cannot find env var AWS_SAM_STACK_NAME. \n"
                "Please setup this environment variable with the stack name where we are running integration tests."
            )

        return stack_name

    def setUp(self) -> None:
        """
        Based on the provided env variable AWS_SAM_STACK_NAME,
        here we use cloudformation API to find out what resources it holds
        """
        stack_name = TestApiGateway.get_stack_name()

        client = boto3.client("cloudformation")

        try:
            response = client.list_stack_resources(StackName=stack_name)
        except Exception as e:
            raise Exception(f'Cannot find stackname {stack_name} - {e}')

        self.stack_resources = response['StackResourceSummaries']

    def test_status_resources(self):
        """
            Test all resources in cloudformation stack has valid status
        """
        VALID_STATUS = ['CREATE_COMPLETE', 'UPDATE_COMPLETE']
        self.assertEqual(all([True if res['ResourceStatus'] in VALID_STATUS else False for res in self.stack_resources]), True)
