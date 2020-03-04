import boto3
import os
import json

# AWS SDK CLIENTS
sqs_client = boto3.client("sqs")
dynamo_client = boto3.client('dynamodb')
event_client = boto3.client('events')

# Function handler
def handler(event, context):
    for record in event['Records']:
        body = json.loads(record["body"])
        # Form body of detail for event
        entry = {
            "item": body["item"],
            "channel": body["channel"]
        }
        # Send event to event bus
        put_events_response = event_client.put_events(
            Entries=[
                {
                    "Source": body["source"],
                    "Detail": json.dumps(entry),
                    "EventBusName": os.environ["EVENT_BUS_NAME"],
                    "DetailType": "New RSS Item"
                }
            ]
        )
        print(put_events_response)
        # Record that this item has been processed by creating a row 
        # in the DynamoDB table
        dynamo_client.put_item(
            TableName=os.environ["DYNAMO_TABLE"],
            Item={
                "source": {
                    "S": body["source"]
                },
                "guid": {
                    "S": body["item"]["guid"]
                }
            }
        )
        # Delete this message if it is processed successully 
        sqs_client.delete_message(
            QueueUrl=os.environ["ITEM_QUEUE_URL"],
            ReceiptHandle=record["receiptHandle"]
        )