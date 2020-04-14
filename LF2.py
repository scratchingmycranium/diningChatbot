from __future__ import print_function

import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError
from botocore.vendored import requests
import urllib3
import random


def lambda_handler(event, context):
    sqs = boto3.client('sqs')
    messageMasterList = []
    
    response = sqs.receive_message(QueueUrl="",
                                       MaxNumberOfMessages=10,
                                       WaitTimeSeconds=0,
                                       MessageAttributeNames=['All']
                                       )
                                       
                                       
    if 'Messages' in response:
        
        Messages = response["Messages"]
        
        for msg in Messages:
            messageDeets ={
                'MessageId': msg['MessageId'],
                'Body': json.loads(msg['Body'])
            }
            messageMasterList.append(messageDeets)
            sqs.delete_message(QueueUrl="",ReceiptHandle=msg["ReceiptHandle"])
            
        for msg in messageMasterList:
            location = msg['Body']["location"]
            time = msg['Body']["time"]
            num_ppl = msg['Body']["num_ppl"]
            phone_num = msg['Body']['phone_num']
            cuisine = msg['Body']["cuisine"]
            name = "Generic Restaurant"
            address = "Generic Address"
            
            restNameAddr = getDynamoData(cuisine)
            
            foodSuggestions(phone_num, location, restNameAddr[0], cuisine, restNameAddr[1])
            
    else:
         return None
    
    
     
def sendSMS(resultData, phone_number):
    sns_client = boto3.client('sns',aws_access_key_id="", aws_secret_access_key="",region_name="us-east-1")
    response = sns_client.publish(
                                  PhoneNumber = "+1" + phone_number,
                                  Message=resultData
                                )

    
def foodSuggestions(phone_num, location, name, cuisine, address):
    
    
    sendMessage = "Hello! Here is a suggestion in {} for a {} restaurant called {} located at {}.".format(location, cuisine, name, address)
    sendSMS(sendMessage, phone_num)
    
def getDynamoData(cuisine):
    
    client = boto3.resource('dynamodb',
                            aws_access_key_id='',
                            aws_secret_access_key='',
                            region_name='us-east-1'
                            )
    table = client.Table('yelp-restaurants')
    
    cuisine = cuisine.lower()
    
    cuisineList = restData[cuisine]

    idKey = random.choice(cuisineList)
    
    responseData = table.query(KeyConditionExpression=Key('id').eq(idKey))
    
    restDataToSend = []
    restDataToSend.append(responseData['Items'][0]['name'])
    restDataToSend.append(responseData['Items'][0]['displayAddr'])
    
    return restDataToSend
