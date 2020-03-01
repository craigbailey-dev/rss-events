import boto3
import os
import json
import urllib
import urllib.parse
import urllib.request
import urllib.error
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime
import hashlib

sqs_client = boto3.client("sqs")
dynamo_client = boto3.client('dynamodb')

def parse_rss(text):
    root = ET.fromstring(text)
    channel_properties = {}
    items = []
    for element in root.findall('./channel/'):
        if element.tag == "item":
            item = {}
            for item_element in element:
                if item_element.tag == "category":
                    item.setdefault("itemCategories", [])
                    item["itemCategories"].append(item_element.text)
                elif item_element.tag == "title":
                    item["itemTitle"] = item_element.text
                elif item_element.tag == "link":
                    item["itemLink"] = item_element.text
                elif item_element.tag == "description":
                    item["itemDescription"] = item_element.text 
                elif item_element.tag == "author":
                    item["itemAuthor"] = item_element.text 
                elif item_element.tag == "comments":
                    item["itemComments"] = item_element.text 
                elif item_element.tag == "guid":
                    item["itemGuid"] = item_element.text 
                elif item_element.tag == "pubDate":
                    item["itemPubDate"] = datetime.strptime(item_element.text, "%a, %d %b %Y %H:%M:%S %z").isoformat()
                elif item_element.tag == "enclosure":
                    item["itemenClosure"] = item_element.attrib 
                elif item_element.tag == "source":
                    item["itemSource"] = item_element.attrib 
                    item["itemSource"]["name"] = item_element.text
            items.append(item)
        elif element.tag == "category":
            channel_properties.setdefault("channelCategories", [])
            channel_properties["channelCategories"].append(element.text)
        elif element.tag == "title":
            channel_properties["channelTitle"] = element.text
        elif element.tag == "link":
            channel_properties["channelLink"] = element.text
        elif element.tag == "description":
            channel_properties["channelDescription"] = element.text 
        elif element.tag == "language":
            channel_properties["channelLanguage"] = element.text  
        elif element.tag == "copyright":
            channel_properties["channelCopyright"] = element.text   
        elif element.tag == "managingEditor":
            channel_properties["channelManagingEditor"] = element.text 
        elif element.tag == "webMaster":
            channel_properties["channelWebMaster"] = element.text 
        elif element.tag == "pubDate":
            channel_properties["channelPubDate"] = datetime.strptime(element.text, "%a, %d %b %Y %H:%M:%S %z").isoformat()
        elif element.tag == "lastBuildDate":
            channel_properties["channelLastBuildDate"] = datetime.strptime(element.text, "%a, %d %b %Y %H:%M:%S %z").isoformat() 
        elif element.tag == "generator":
            channel_properties["channelGenerator"] = element.text 
        elif element.tag == "docs":
            channel_properties["channelDocs"] = element.text
        elif element.tag == "cloud":
            channel_properties["channelCloud"] = element.attrib
        elif element.tag == "ttl":
            channel_properties["channelTtl"] = int(element.text)
        elif element.tag == "image":
            channel_properties["channelImage"] = {}
            for image_element in element:
                if image_element.tag == "url":
                    channel_properties["channelImage"]["url"] = image_element.text
                if image_element.tag == "title":
                    channel_properties["channelImage"]["title"] = image_element.text
                if image_element.tag == "link":
                    channel_properties["channelImage"]["link"] = image_element.text
                if image_element.tag == "width":
                    channel_properties["channelImage"]["width"] = int(image_element.text)
                if image_element.tag == "height":
                    channel_properties["channelImage"]["height"] = int(image_element.text)
                if image_element.tag == "description":
                    channel_properties["channelImage"]["description"] = image_element.text
        elif element.tag == "rating":
            channel_properties["channelRating"] = element.text
        elif element.tag == "textInput":
            channel_properties["channelTextInput"] = {}
            for text_input_element in element:
                if text_input_element.tag == "name":
                    channel_properties["channelTextInput"]["name"] = text_input_element.text
                if text_input_element.tag == "title":
                    channel_properties["channelTextInput"]["title"] = text_input_element.text
                if text_input_element.tag == "link":
                    channel_properties["channelTextInput"]["link"] = text_input_element.text
                if text_input_element.tag == "description":
                    channel_properties["channelTextInput"]["description"] = text_input_element.text
        elif element.tag == "skipHours":
            channel_properties["channelSkipHours"] = [int(hour.text) for hour in root.findall('./channel/skipHours/hour')]
        elif element.tag == "skipDays":
            channel_properties["channelSkipDays"] = [day.text for day in root.findall('./channel/skipDays/day')]
    return channel_properties, items
 

def list_guids(source):
    guids = set()
    next_key = "?"
    while next_key: 
        query_request = {
            "TableName" : os.environ["DYNAMO_TABLE"],
            "ExpressionAttributeNames" : {
                "#S" : "source",
                "#G" : "guid"
            },
            "ExpressionAttributeValues" : {
                ":source" : {
                    "S" : source
                }
            },
            "KeyConditionExpression" : "#S = :source",
            "ProjectionExpression" : "#G"
        }
        if next_key != "?":
            query_request["ExclusiveStartKey"] = next_key
        query_response = dynamo_client.query(**query_request)
        if query_response["Count"] > 0:
            guids = guids.union([item["guid"]["S"] for item in query_response["Items"]])
        next_key = query_response["LastEvaluatedKey"] if "LastEvaluatedKey" in query_response else None
    return guids


def handler(event, context):
    for record in event['Records']:
        try:
            source = record["body"]
            response = urllib.request.urlopen(source)
            channel_attributes, items = parse_rss(response.read().decode("utf-8"))
            guids = list_guids(source)
            new_items = [item for item in items if item["itemGuid"] not in guids]
            for item in new_items:
                try:
                    message_hash = hashlib.md5("{}{}".format(source,item["itemGuid"]).encode("utf-8")).hexdigest()
                    sqs_client.send_message(
                        QueueUrl=os.environ["ITEM_QUEUE_URL"],
                        MessageBody=json.dumps({
                            "source": source,
                            "channel": channel_attributes,
                            "item": item
                        }),
                        MessageDeduplicationId=message_hash,
                        MessageGroupId=message_hash
                    )
                except:
                    traceback.print_exc()
        except:
            traceback.print_exc()
        finally:
            sqs_client.delete_message(
                QueueUrl=os.environ["CHANNEL_QUEUE_URL"],
                ReceiptHandle=record["receiptHandle"]
            )