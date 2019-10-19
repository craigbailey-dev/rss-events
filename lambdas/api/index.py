import boto3
import os
import json
import awsgi
from botocore.exceptions import ClientError 
from flask import (
    Flask, 
    jsonify, 
    request, 
    Response
)
from dynamodb_json import json_util as dynamo_json

app = Flask(__name__)

dynamo_client = boto3.client("dynamodb")
sns_client = boto3.client("sns")

def handle_generic_error(e): 
    traceback.print_exc() 
    return Response( 
        json.dumps({ 
            "Error" : { 
                "Message" : str(e), 
                "Type" : "Internal" 
            } 
        }), 
        status=502 
    ) 
 
 
def handle_boto3_error(ce): 
    traceback.print_exc() 
    code = ce.response['Error']['Code'] if 'Code' in ce.response['Error'] else '[Code not found]' 
    message = ce.response['Error']['Message'] if 'Message' in ce.response['Error'] else '[Message not found]' 
    err_type = ce.response['Error']['Type'] if 'Type' in ce.response['Error'] else '[Type not found]' 
    return Response( 
        json.dumps({ 
            "Error" : { 
                "Message" : "{}: {}".format(code, message), 
                "Type" : err_type 
            } 
        }), 
        status=ce.response['ResponseMetadata']['HTTPStatusCode'] 
    )
    

@app.route('/sources', methods=["GET"])
def list_sources():
    try: 
        sources = []
        next_scan_key = "?"
        while next_scan_key:
            scan_request = {
                "TableName" : os.environ["DYNAMO_TABLE"]
            }
            if next_scan_key != "?":
                request["ExclusiveStartKey"] = next_scan_key
            scan_response = dynamo_client.scan(**scan_request)
            if scan_response["Count"] != 0:
                sources.extend([
                    dynamo_json.loads(item, as_dict=True)
                    for item in scan_response['Items']
                ])
            next_scan_key = scan_response["LastEvaluatedKey"] if "LastEvaluatedKey" in scan_response else None
        return {
            "Sources" : sources
        }
    except ClientError as ce: 
        return handle_boto3_error(ce) 
    except Exception as e: 
        return handle_generic_error(e) 


@app.route('/sources', methods=["POST"])
def create_source():
    try: 
        request_body = request.get_json(force=True) 
        if "source" not in request_body:
            return jsonify(status=400, message="Missing required property 'source'") 
        dynamo_client.put_item(
            TableName=os.environ["DYNAMO_TABLE"],
            Item={
                "source" : {
                    "S" : request_body["source"]
                }
            }
        )
        return {"Message" : "Success"}
    except ClientError as ce: 
        return handle_boto3_error(ce) 
    except Exception as e: 
        return handle_generic_error(e)



@app.route('/sources', methods=["DELETE"])
def delete_source():
    try: 
        request_body = request.get_json(force=True) 
        if "source" not in request_body:
            return jsonify(status=400, message="Missing required property 'source'")
        dynamo_client.delete_item(
            TableName=os.environ["DYNAMO_TABLE"],
            Key={
                "source" : {
                    "S" : request_body["source"]
                }
            }
        )
        return {"Message" : "Success"}
    except ClientError as ce: 
        return handle_boto3_error(ce) 
    except Exception as e: 
        return handle_generic_error(e)


@app.route('/subscriptions', methods=["GET"])
def list_subscriptions():
    try: 
        subscriptions = []
        next_token = "?"
        while next_token:
            list_request = {
                TopicArn: os.environ["TOPIC_ARN"]
            }
            if next_token != "?":
                list_request["NextToken"] = next_token
            list_response = sns_client.list_subscriptions_by_topic(**list_request)
            subscriptions.extend(list_response["Subscriptions"])
            next_token = list_response["NextToken"] if "NextToken" in list_response else None
        return {"Subscriptions" : subscriptions}
    except ClientError as ce: 
        return handle_boto3_error(ce) 
    except Exception as e: 
        return handle_generic_error(e) 


@app.route('/subscriptions', methods=["POST"])
def create_subscription():
    try: 
        return {"Message" : "Success"}
    except ClientError as ce: 
        return handle_boto3_error(ce) 
    except Exception as e: 
        return handle_generic_error(e)


@app.route('/subscriptions/<id>', methods=["DELETE"])
def delete_subscription(id):
    try: 
        return {"Message" : "Success"}
    except ClientError as ce: 
        return handle_boto3_error(ce) 
    except Exception as e: 
        return handle_generic_error(e)


def handler(event, context):
    response = awsgi.response(app, event, context) 
    if "headers" in response: 
        response["headers"]["Access-Control-Allow-Origin"] = "*" 
    else: 
        response["headers"] = { "Access-Control-Allow-Origin" : "*" } 
    return response 