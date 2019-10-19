import boto3
import json
import os
import traceback

dynamo_client = boto3.client('dynamodb')
sqs_client = boto3.client('sqs')

def handler(event, context):
    next_scan_key = "?"
    while next_scan_key:
        scan_request = {
            "TableName" : os.environ["DYNAMO_TABLE"]
        }
        if next_scan_key != "?":
            request["ExclusiveStartKey"] = next_scan_key
        scan_response = dynamo_client.scan(**scan_request)
        if scan_response["Count"] != 0:
            for item in scan_response["Items"]:
                try:
                    sqs_client.send_message(
                        QueueUrl=os.environ["QUEUE_URL"],
                        MessageBody=item["source"]["S"]
                    )
                except:
                    traceback.print_exc()
        next_scan_key = scan_response["LastEvaluatedKey"] if "LastEvaluatedKey" in scan_response else None