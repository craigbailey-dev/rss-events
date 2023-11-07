import boto3
import os
import json
import urllib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import hashlib
import time
import traceback

# AWS SDK CLIENTS
sqs_client = boto3.client("sqs")
dynamo_client = boto3.client('dynamodb')

# Parse XML content of RSS feed
def parse_rss(text):
    root = ET.fromstring(text)
    channel_properties = {}
    items = []
    # Parse all elements in channel
    for element in root.findall('./channel/'):
        if element.tag == "item":
            item = {}
            for item_element in element:
                # Only extract supported item elements
                if item_element.tag == "category":
                    item.setdefault("categories", [])
                    item["categories"].append(item_element.text)
                elif item_element.tag == "title":
                    item["title"] = item_element.text
                elif item_element.tag == "link":
                    item["link"] = item_element.text
                elif item_element.tag == "description":
                    item["description"] = item_element.text 
                elif item_element.tag == "author":
                    item["author"] = item_element.text 
                elif item_element.tag == "comments":
                    item["comments"] = item_element.text 
                elif item_element.tag == "guid":
                    item["guid"] = item_element.text 
                elif item_element.tag == "pubDate":
                    item["pubDate"] = item_element.text
                elif item_element.tag == "enclosure":
                    item["enclosure"] = item_element.attrib 
                elif item_element.tag == "source":
                    item["source"] = item_element.attrib 
                    item["source"]["name"] = item_element.text
            items.append(item)
        # Only extract supported channel elements
        elif element.tag == "category":
            channel_properties.setdefault("categories", [])
            channel_properties["categories"].append(element.text)
        elif element.tag == "title":
            channel_properties["title"] = element.text
        elif element.tag == "link":
            channel_properties["link"] = element.text
        elif element.tag == "description":
            channel_properties["description"] = element.text 
        elif element.tag == "language":
            channel_properties["language"] = element.text  
        elif element.tag == "copyright":
            channel_properties["copyright"] = element.text   
        elif element.tag == "managingEditor":
            channel_properties["managingEditor"] = element.text 
        elif element.tag == "webMaster":
            channel_properties["webMaster"] = element.text 
        elif element.tag == "pubDate":
            channel_properties["pubDate"] = element.text
        elif element.tag == "lastBuildDate":
            channel_properties["lastBuildDate"] = element.text
        elif element.tag == "generator":
            channel_properties["generator"] = element.text 
        elif element.tag == "docs":
            channel_properties["docs"] = element.text
        elif element.tag == "cloud":
            channel_properties["cloud"] = element.attrib
        elif element.tag == "ttl":
            channel_properties["ttl"] = int(element.text)
        elif element.tag == "image":
            channel_properties["image"] = {}
            for image_element in element:
                if image_element.tag == "url":
                    channel_properties["image"]["url"] = image_element.text
                if image_element.tag == "title":
                    channel_properties["image"]["title"] = image_element.text
                if image_element.tag == "link":
                    channel_properties["image"]["link"] = image_element.text
                if image_element.tag == "width":
                    channel_properties["image"]["width"] = int(image_element.text)
                if image_element.tag == "height":
                    channel_properties["image"]["height"] = int(image_element.text)
                if image_element.tag == "description":
                    channel_properties["image"]["description"] = image_element.text
        elif element.tag == "rating":
            channel_properties["rating"] = element.text
        elif element.tag == "textInput":
            channel_properties["textInput"] = {}
            for text_input_element in element:
                if text_input_element.tag == "name":
                    channel_properties["textInput"]["name"] = text_input_element.text
                if text_input_element.tag == "title":
                    channel_properties["textInput"]["title"] = text_input_element.text
                if text_input_element.tag == "link":
                    channel_properties["textInput"]["link"] = text_input_element.text
                if text_input_element.tag == "description":
                    channel_properties["textInput"]["description"] = text_input_element.text
        elif element.tag == "skipHours":
            channel_properties["skipHours"] = [int(hour.text) for hour in root.findall('./channel/skipHours/hour')]
        elif element.tag == "skipDays":
            channel_properties["skipDays"] = [day.text for day in root.findall('./channel/skipDays/day')]
    # Return channel element values and channel items
    return channel_properties, items


#Parse XML content of Atom feed (.atom RSS feeds)
def atom_parser(text):
    channel_properties = {}
    items = []

    root = ET.fromstring(text)
    atom_namespace = root.tag.split('}')[0][1:]
    atom_xmlns = f"{{{atom_namespace}}}"

    for element in root.findall(f"{atom_xmlns}entry"):
        item = {}
        item["title"] = element.find(f"{atom_xmlns}title").text
        item["description"] = element.find(f"{atom_xmlns}summary").text
        item["source"] = root.find((f"{atom_xmlns}link[@rel='self']")).attrib['href']
        item["guid"] = root.find(f"{atom_xmlns}link[@rel='alternate']").attrib['href']
        items.append(item)


    channel_properties["title"] = root.find(f"{atom_xmlns}title").text
    channel_properties["link"] = root.find(f"{atom_xmlns}link[@rel='alternate']").attrib['href']
    channel_properties["language"] = 'en-us'

    subtitle_element = root.find(f"{atom_xmlns}subtitle")
    if subtitle_element is not None:
        channel_properties["description"] = subtitle_element.text

    generator_element = root.find(f"{atom_xmlns}generator")
    if generator_element is not None:
        channel_properties["generator"] = generator_element.text

    updated_element = root.find(f"{atom_xmlns}updated")
    if updated_element is not None:
        channel_properties["updated"] = updated_element.text

    author_element = root.find(f"{atom_xmlns}author/name")
    if author_element is not None:
        channel_properties["author"] = author_element.text

    return channel_properties, items

# List the guids of all channel items from this source that have already been sent 
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


# Delete channel items that are no longer visible in the channel
def delete_old_items(source, old_item_guids):
    for i in range(0, len(old_item_guids), 25):
        time_wait = 0.05
        batch = old_item_guids[i:i+25]
        unprocessed_items = {
            os.environ["DYNAMO_TABLE"]: [
                {
                    "DeleteRequest": {
                        "Key": {
                            "source": {
                                "S": source
                            },
                            "guid": {
                                "S": item
                            },
                        }
                    }
                }
                for item in batch
            ]
        }
        while unprocessed_items and len(unprocessed_items) > 0 and time_wait < 1:
            delete_response = dynamo_client.batch_write_item(RequestItems=unprocessed_items)
            unprocessed_items = delete_response.get("UnprocessedItems")
            time.sleep(time_wait)
            time_wait = time_wait * 2


# Send new channel items to another queue to be processed
def send_queue_messages(source, channel_attributes, new_items):
    for item in new_items:
        try:
            # Create hash of message to prevent deduplication
            message_hash = hashlib.md5("{}{}".format(source, item["guid"]).encode("utf-8")).hexdigest()
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
            print("Error sending queue message for item")
            print("Item:", item)
            traceback.print_exc()


# Function handler
def handler(event, context):
    for record in event['Records']:
        try:
            sqs_message = json.loads(record["body"])
            source = sqs_message["source"]
            request_headers = sqs_message.get("headers")
            # Make HTTP request to get RSS feed content   
            request = urllib.request.Request(source)
            if request_headers:
                for header, value in request_headers.items():
                    request.add_header(header, value)
            response = urllib.request.urlopen(request)
            # Extract channel attributes and channel items
            channel_attributes, items = parse_rss(response.read().decode("utf-8"))
            # Obtain guids of current channel items and already-processed channel items
            item_guids = set([item["guid"] for item in items])
            stored_guids = list_guids(source)
            new_item_guids = item_guids.difference(stored_guids)
            old_item_guids = list(stored_guids.difference(item_guids))
            new_items = [item for item in items if item["guid"] in new_item_guids]
            # Process new items, delete old items
            send_queue_messages(source, channel_attributes, new_items)
            delete_old_items(source, old_item_guids)
        except:
            print("Error processing source")
            traceback.print_exc()
        finally:
            # Always delete message from queue, even in an error. 
            # Parsing this RSS source can be tried again later
            sqs_client.delete_message(
                QueueUrl=os.environ["CHANNEL_QUEUE_URL"],
                ReceiptHandle=record["receiptHandle"]
            )