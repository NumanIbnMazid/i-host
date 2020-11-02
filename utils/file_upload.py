import uuid

import boto3
from botocore.exceptions import ClientError
from django.conf import settings

# from sentry_sdk.integrations import logging


def file_upload(file_name, object_name=None):
    """Upload a file to an S3 bucket

    :param file_name: File to upload
    :param object_name: S3 object name.
    :return: uploaded file link,  else None
    """

    # If S3 object_name was not specified, create new name
    root_path = settings.MEDIA_ROOT

    if object_name is None:
        object_name = (
            root_path + "/" + uuid.uuid4().__str__() + "_" + file_name
        )
    else:
        object_name = object_name.replace('media', root_path)

    # boto3 setup
    s3_client = boto3.client(
        's3',
        region_name='sgp1',   # digital Ocean
        endpoint_url='https://sgp1.digitaloceanspaces.com',  # digital Ocean
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    domain = settings.AWS_S3_CUSTOM_DOMAIN    # digital Ocean
    # region = settings.REGION_NAME           #AWS

    # file upload
    try:
        response = s3_client.upload_file(
            file_name, bucket, object_name, ExtraArgs={"ACL": "public-read"}
        )
        # Digital Ocean
        url = "https://sgp1.digitaloceanspaces.com/%s/%s" % (
            bucket, object_name)
        # url = "https://%s.%s.amazonaws.com/%s" % (bucket, region, object_name)         #AWS
    except ClientError as e:
        # logging.error(e)
        url = None

    return url


def file_delete(url):
    """Delete a file to an S3 bucket

    :param url: File to delete
    :return: space response
    """

    # boto3 setup
    s3_client = boto3.client(
        's3',
        region_name='sgp1',   # digital Ocean
        endpoint_url='https://sgp1.digitaloceanspaces.com',  # digital Ocean
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    bucket = settings.AWS_STORAGE_BUCKET_NAME
    # domain = settings.AWS_S3_CUSTOM_DOMAIN    # digital Ocean
    # region = settings.REGION_NAME           #AWS
    url_prefix = "https://sgp1.digitaloceanspaces.com/%s/" % (bucket)
    object_name = url.replace(url_prefix, '')

    # file upload
    try:
        response = s3_client.delete_object(
            Bucket=bucket,
            Key=object_name,
        )
        # Digital Ocean
        # url = "https://%s.%s.amazonaws.com/%s" % (bucket, region, object_name)         #AWS
    except ClientError:
        # logging.error(e)
        response = None

    return response
