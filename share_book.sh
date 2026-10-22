#!/bin/bash
set -euo pipefail

#Getting three positional command line args
URL=$1
BUCKET=$2
EXP=$3

#Getting file name from url, defining folder name, and defining the book path
FILENAME="$(basename "$URL")"
DEST_DIR="books"
BOOK_PATH="$DEST_DIR/$FILENAME"

#Creating books folder if it doesn't exist and downloading book into books folder
mkdir -p "$DEST_DIR"
curl -fsSL -o "$BOOK_PATH" "$URL"

#Creating the bucket unless it already exists
if aws s3 ls "s3://$BUCKET" > /dev/null 2>&1; then
    echo "Bucket $BUCKET already exists, reusing it"
else
    aws s3 mb "s3://$BUCKET"
fi

#Uploading the book to private bucket
aws s3 cp "$BOOK_PATH" "s3://$BUCKET/$FILENAME" \
    --content-type "text/plain; charset=utf-8"

#Presigning URL to the book
aws s3 presign "s3://$BUCKET/$FILENAME" --expires-in "$EXP"