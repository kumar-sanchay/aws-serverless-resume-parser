# aws-serverless-resume-parser

This project contains source code and supporting files for a serverless application resume-parser-app that you can deploy with the SAM CLI. 

This project mainly consists of sam template(template.yaml) used for creating infratructure in aws.
AWS serverless services used in this project:
- AWS Lambda and Layers
- AWS API Gateway
- AWS DynamoDB
- AWS s3

Roles and policies attached to this services has only necessary permission.
Lambda functions is return in python programming language.
Layers consists of neccsary python packages required by lambda functions.

This project mainly consists of 3 lambda functions

1) Upload Resume to S3
   This will be used with an api in api gateway to upload resume files on S3.

2) Process Resume
   This lambda function will be invoked by S3 on object creation event.
   This lambda function will extract data poits from resume file and store it in dynamo db.

3) Get Resume
   This lambda function will be used with an api in api gateway.
   This will query the dynamo db based on parameters and will return the captured data points.
   It will also return resume pre-signed url stored in s3 which will expire after a timeout.
