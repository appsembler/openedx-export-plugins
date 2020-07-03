"""
File storage routines for openedx_export_plugins Django app.
"""

import logging

import boto
from boto.s3.key import Key

from app_settings import AWS_ID, AWS_KEY


logger = logging.getLogger(__name__)


def do_store_s3(tmp_fn, storage_location, bucketname, overwrite=False):
    """ handle Amazon S3 storage for generated files
    """
    local_path = tmp_fn
    dest_path = storage_location

    s3_conn = boto.connect_s3(AWS_ID, AWS_KEY)
    bucket = s3_conn.get_bucket(bucketname)
    key = Key(bucket, name=dest_path)
    key.set_contents_from_filename(local_path)
    logger.info("uploaded {local} to S3 bucket {bucketname}/{s3path}".format(
            local=local_path, bucketname=bucketname, s3path=dest_path
    ))
