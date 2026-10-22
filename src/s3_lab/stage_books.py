#!/usr/bin/env python3

import logging
import requests
import os
import sys
import boto3
import json
import time
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

s3 = boto3.client("s3", region_name="us-east-1")

def parse_args():
    if len(sys.argv) < 4:
        log.error(f"Usage error: fewer than three args")
        sys.exit(1)
    list_file = sys.argv[1]
    index_path = sys.argv[2]
    bucket = sys.argv[3]
    return (list_file, index_path, bucket)

def download_books(list_file, dest_dir):
    """
    Downloads the books listed in list_file into dest_dir and returns a list of local paths
    """
    os.makedirs(dest_dir, exist_ok=True)

    with open(list_file, encoding="utf-8") as file:
        urls = [line.strip() for line in file if line.strip()]
    book_paths = []

    for url in urls:
        name = url.rstrip("/").split("/")[-1]
        path = os.path.join(dest_dir, name)
    
        if os.path.exists(path):
            log.info(f"{path} already exists, skipping download")
            book_paths.append(path)
            continue
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # raises for HTTP errors like 404
        except requests.RequestException as e:
            log.error(f"Failed to download {url}: {e}")
            continue
        with open(path, "wb") as f:
            f.write(response.content)
        log.info(f"Saved {path}")
        book_paths.append(path)
    return book_paths
    

def create_bucket(bucket):
    try:
        s3.head_bucket(Bucket=bucket)
        return True
    except:
        log.error(f"Bucket {bucket} does not exist")
    
    try:
        s3.create_bucket(Bucket=bucket)
        log.info(f"Created bucket: {bucket}")
        return True
    except ClientError as e:
        log.error(f"Error creating bucket {bucket}: {e}")
    return False

def make_public(bucket):
    policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::public-qmm2bx/*"
    }]}
    try:
        s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
        "BlockPublicAcls": False,
        "IgnorePublicAcls": False,
        "BlockPublicPolicy": False,
        "RestrictPublicBuckets": False,
        }, )
    
        s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
        log.info(f"Made bucket {bucket} public")
        return True
    except ClientError as e:
        log.error(f"Error making bucket {bucket} public: {e} ")
        return False


def upload_files(bucket, file_paths):
    count = 0
    for path in file_paths:
        key = os.path.basename(path)
        with open(path, "rb") as f:
            try:
                s3.put_object(
                Bucket=bucket,
                Key=key,
                Body=f,
                ContentType = "text/plain; charset=utf-8"
                )
                log.info(f"Uploaded {path} to s3://{bucket}/{key}")
                count += 1
        
            except ClientError as e:
                log.error(f"Error uploading {path}: {e}")
    return count

def upload_index(bucket, index_path):
    try:
        key = "index.html"
        with open(index_path, "rb") as f:
            s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=f,
            ContentType="text/html",
                )
        log.info(f"Uploaded {index_path} to s3://{bucket}/{key}")
        return True

    except FileNotFoundError:
        log.error(f"Local file not found: {index_path}")
        return False
    except ClientError as e:
        log.error(f"Error uploading {index_path}: {e}")
        return False

def main():
    list_file, index_path, bucket = parse_args()
    paths = download_books(list_file, "books")
    if len(paths) == 0:
        log.error("No books were downloaded")
        sys.exit(1)
    created = create_bucket(bucket)
    if created == False:
        log.error("Bucket could not be created")
        sys.exit(1)
    public = make_public(bucket)
    if public == False:
        log.error("Bucket could not be made public")
        sys.exit(1)
    files = upload_files(bucket, paths)
    index_uploaded = upload_index(bucket, index_path)
    
    log.info(f"Success. URL: https://{bucket}.s3.amazonaws.com/index.html")

if __name__ == "__main__":
    main()