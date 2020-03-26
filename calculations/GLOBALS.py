from pymongo import MongoClient

connect_string = "mongodb+srv://digdesign:<Diggit123>@cluster0-t0vfo.mongodb.net/test?retryWrites=true&w=majority"
client = MongoClient(connect_string)

#
#
# import boto3
# import os
# import os.path as path
#
#
#
# db_dict = {}
#
# #global constants
# AWS = False #flip this on or off
# BUCKET = 'dig-geojson'
#
# #rootkey.csv must not be included in Github for AWS security reasons. Can be downloaded from AWS.
# AWS_ACCESS_KEY_ID = AWS_SECRET_ACCESS_KEY = None
# if AWS:
#     rootkey = open('rootkey.csv', 'r').readlines()
#     AWS_ACCESS_KEY_ID = (rootkey[0].split("="))[1].strip()
#     AWS_SECRET_ACCESS_KEY = (rootkey[1].split("="))[1].strip()
#
# s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
#
# _default_encoding = 'windows-1252'
# _aws_parent_dir = 'static/data/'
# _local_parent_dir = path.abspath(path.join(__file__, "../..")) + "/data/"
#
# def _get_s3_file(key, bucket=BUCKET, encoding=_default_encoding):
#     if not key.startswith(_aws_parent_dir):
#         key = _aws_parent_dir +  key
#     s3_object = s3.get_object(Bucket=bucket, Key=key)
#     return s3_object['Body'].read().decode(encoding).splitlines()
#
# def _get_s3_file_list(key_prefix, bucket=BUCKET):
#     s3_paginator = s3.get_paginator('list_objects_v2')
#     s3_bucket = s3_paginator.paginate(Bucket=bucket, Prefix=key_prefix)
#     file_list = []
#     for page in s3_bucket:
#         if page['KeyCount'] > 0:
#             for item in page['Contents']:
#                 file_list.append(item['Key'])
#     return file_list
#
# def get_file(file_dir, bucket=BUCKET, encoding=_default_encoding):
#     if AWS:
#         return _get_s3_file(file_dir, bucket=bucket, encoding=encoding)
#     else:
#         file_path = _local_parent_dir + file_dir
#         return open(file_path, 'r', encoding=encoding)
#
# def get_file_list(file_dir, bucket=BUCKET):
#     if not (file_dir.endswith('/') or file_dir.endswith('\\')):
#         file_dir = file_dir + '/'
#     if AWS:
#         return _get_s3_file_list(_aws_parent_dir + file_dir, bucket=bucket)
#     else:
#         return [file_dir + f for f in os.listdir(_local_parent_dir + file_dir)]