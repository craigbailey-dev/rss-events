import boto3
import json
import os
import traceback

# AWS SDK CLIENTS
dynamo_client = boto3.client('dynamodb')
sqs_client = boto3.client('sqs')

# Function handler
def handler(event, context):
    next_scan_key = "?"
    while next_scan_key:
        # Scan sources table 
        scan_request = {
            "TableName" : os.environ["DYNAMO_TABLE"]
        }
        if next_scan_key != "?":
            scan_request["ExclusiveStartKey"] = next_scan_key
        scan_response = dynamo_client.scan(**scan_request)
        if scan_response["Count"] != 0:
            # For each source found in table, send message to queue for processing
            for item in scan_response["Items"]:
                try:
                    message = {
                        "source": item["source"]["S"]
                    }
                    if item.get("httpHeaderOverrides"):
                        message["headers"] = { key: value["S"] for key, value in item["httpHeaderOverrides"]["M"].items() }
                    sqs_client.send_message(
                        QueueUrl=os.environ["QUEUE_URL"],
                        MessageBody=json.dumps(message)
                    )
                except:
                    traceback.print_exc()               
        next_scan_key = scan_response["LastEvaluatedKey"] if "LastEvaluatedKey" in scan_response else None
