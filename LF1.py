from urllib.request import Request, urlopen
import json
import os
import time
import datetime
import dateutil.parser
import math
import logging
from random import choice
import re
import boto3

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }
    
def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }
def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }

    return response

def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')
        
def get_slots(intent_request):
    return intent_request['currentIntent']['slots']

def thanks_intent(intent_request):
    thanks_response_list = [
        'You are very welcome',
        'No problem, have a nice day!',
        'No, thank YOU!'
    ]
    if(intent_request["invocationSource"] == "FulfillmentCodeHook"):
        return{
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                    "content": choice(thanks_response_list)
                }
            }
        }
def welcome_message(intent_request):
    greeting_response_list = [
        'Hi there!',
        'Hi there! How can I help you?',
        'Hello!'
    ]
    if(intent_request["invocationSource"] == "FulfillmentCodeHook"):
        return{
            "dialogAction": {
                "type": "Close",
                "fulfillmentState": "Fulfilled",
                "message": {
                    "contentType": "PlainText",
                    "content": choice(greeting_response_list)
                }
            }
        }
def validate_query(location, cuisine, time, num_ppl, phone_num):
    locationList = ["new york", "brooklyn", "rego Park", "manhattan", "long island city", "jersey city","forest hills"]
    cuisineList = ["chinese", "italian", "mexican", "kosher", "mideastern", "cantonese","japanese", "thai"]
    
    if location is not None and location.lower() not in locationList:
        return build_validation_result(False, "Location", "Valid locations: new York, brooklyn, rego Park, manhattan, long island city, jersey city, forest hills")
        
    if cuisine is not None and cuisine.lower() not in cuisineList:
        return build_validation_result(False, "Cuisine", "Valid Cuisines: chinese, italian, mexican, kosher, mideastern, cantonese, japanese, thai")
    
    if time is not None:
        if len(time) != 5:
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', "Invalid time format")

        hour, minute = time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            # Not a valid time; use a prompt defined on the build-time model.
            return build_validation_result(False, 'DiningTime', "Invalid time format")
    
    if num_ppl is not None and int(num_ppl) <= 0:
        return build_validation_result(False, "NumPeople", "Please specify size of party > 1")
    
    if phone_num is not None and len(phone_num) != 10:
        return build_validation_result(False, "PhoneNum", "Please enter valid phone number. (eg. 0123456789)")
    
    return build_validation_result(True, None, None)
    

def find_food(intent_request):
    """
    Performs dialog management and fulfillment for ordering flowers.
    Beyond fulfillment, the implementation of this intent demonstrates the use of the elicitSlot dialog action
    in slot validation and re-prompting.
    """

    location = get_slots(intent_request)["Location"]
    time = get_slots(intent_request)["DiningTime"]
    num_ppl = get_slots(intent_request)["NumPeople"]
    phone_num = get_slots(intent_request)["PhoneNum"]
    cuisine = get_slots(intent_request)["Cuisine"]
    source = intent_request['invocationSource']

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt for the first violation detected.
        slots = get_slots(intent_request)
        
        validation_result = validate_query(location, cuisine, time, num_ppl, phone_num)
        
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])


        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

        return delegate(output_session_attributes, get_slots(intent_request))

  
    client = boto3.client('sqs')
    
    response = client.send_message(
        QueueUrl='https://sqs.us-east-1.amazonaws.com/773422078356/Q1',
        MessageBody=json.dumps({
            'location': location,
            'time': time,
            'num_ppl': num_ppl,
            'phone_num': phone_num,
            'cuisine': cuisine
        })
    )
    
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': "That's all! We will send you a text message with a suggestion shortly!"
                 })


def dispatch(intent_request):
    #Called when the user specifies an intent for this bot.
    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'DiningSuggestionsIntent':
        return find_food(intent_request)
    if intent_name == "GreetingIntent":
        return welcome_message(intent_request)
    if intent_name == "ThankYouIntent":
        return thanks_intent(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')


# main handler

def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    
    
    return dispatch(event)
