import boto3
import os

sqs_client = boto3.client("sqs")

def handler(event, context):

    for record in event['Records']:
        sqs_client.delete_message(
            QueueUrl=os.environ["QUEUE_URL"],
            ReceiptHandle=record["receiptHandle"]
        )