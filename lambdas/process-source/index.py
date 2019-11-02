import boto3
import os
import json
import requests
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime
import hashlib

sns_client = boto3.client("sns")
sqs_client = boto3.client("sqs")
dynamo_client = boto3.client('dynamodb')

def parse_xml(filename):
    tree = ET.parse(filename) 
    root = tree.getroot()

    channel_attributes = {}
    items = []

    channel_attributes['channel-categories'] = {
        "DataType": "String.Array",
        "StringValue": json.dumps([
            category.text
            for category in root.findall('./channel/category')
        ])
    }

    for element in root.findall('./channel/'):
        if element.tag == "item":
            item = element
            pub_date = item.find("pubDate").text
            timestamp = int(datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z").timestamp() * 1000)
            guid_text = item.find("guid").text
            guid_hash = hashlib.md5(guid_text.encode('utf-8')).hexdigest()
            items.append({
                "timestamp" : timestamp,
                "guid_hash" : guid_hash,
                "item_text" : ET.tostring(item, , method="xml").decode()
            })
        elif len(element.getchildren()) == 0:
            channel_attributes["channel-" + element.tag] = {
                "DataType": "String",
                "StringValue": element.text 
            }
    return channel_attributes, items


def list_guids(source, timestamp):
    guids = set()
    next_key = "?"
    while next_key: 
        query_request = {
            "TableName" : os.environ["DYNAMO_TABLE"],
            "IndexName" : "timeSorted",
            "ExpressionAttributeNames" : {
                "#S" : "source",
                "#T" : "timestamp",
                "#G" : "guidHash"
            },
            "ExpressionAttributeValues" : {
                ":source" : {
                    "S" : source
                },
                ":timestamp" : {
                    "N" : str(timestamp)
                }
            },
            "KeyConditionExpression" : "#S = :source AND #T >= :timestamp",
            "ProjectionExpression" : "#G"
        }
        if next_key != "?":
            query_request["ExclusiveStartKey"] = next_key
        query_response = dynamo_client.query(**query_request)
        if query_response["Count"] > 0:
            guids = guids.union([item["guidHash"]["S"] for item in query_response["Items"]])
        next_key = query_response["LastEvaluatedKey"] if "LastEvaluatedKey" in query_response else None
    return guids


def handler(event, context):

    for record in event['Records']:
        try:
            filename = "/tmp/{}.xml".format(record["md5OfBody"])
            source = record["body"]
            response = requests.get(source)
            with open(filename, "wb") as outfile:
                outfile.write(response.content)
            channel_attributes, items = parse_xml(filename)
            min_timestamp = min([item["timestamp"] for item in items])
            guids = list_guids(source, min_timestamp)
            new_items = [item for item in items if item["guid_hash"] not in guids]

            for item in new_items:
                try:
                    sns_client.publish(
                        TopicArn=os.environ["TOPIC_ARN"],
                        Message=item["item_text"],
                        MessageAttributes=channel_attributes
                    )
                    dynamo_client.put_item(
                        TableName=os.environ["DYNAMO_TABLE"],
                        Item={
                            "source" : {
                                "S" : source
                            },
                            "guidHash" : {
                                "S" : item["guid_hash"]
                            },
                            "timestamp" : {
                                "N" : str(item["timestamp"])
                            }
                        }
                    )
                except:
                    traceback.print_exc()
                    
            
        except:
            traceback.print_exc()
        sqs_client.delete_message(
            QueueUrl=os.environ["QUEUE_URL"],
            ReceiptHandle=record["receiptHandle"]
        )