import boto3

#global constants
AWS = True #flip this on or off
BUCKET = 'dig-geojson'

#rootkey.csv must not be included in Github for AWS security reasons. Can be downloaded from AWS.
rootkey = open('rootkey.csv', 'r').readlines()

AWS_ACCESS_KEY_ID = (rootkey[0].split("="))[1].strip()
AWS_SECRET_ACCESS_KEY = (rootkey[1].split("="))[1].strip()

def get_s3_file(key, bucket=BUCKET, encoding='utf-8'):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, \
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    s3_object = s3.get_object(Bucket=bucket, Key=key)
    return s3_object['Body'].read().decode(encoding).splitlines()

def get_s3_file_list(key_prefix, bucket=BUCKET):
    s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, \
                      aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
    s3_paginator = s3.get_paginator('list_objects_v2')
    s3_bucket = s3_paginator.paginate(Bucket=bucket, Prefix=key_prefix)

    for page in s3_bucket:
        if page['KeyCount'] > 0:
            for item in page['Contents']:
                yield item['Key']

