import json
import boto3

def lambda_handler(event, context):
    # TODO implement
    message = event['msg']
    client = boto3.client('lex-runtime')

    response = client.post_text(
        botName="diningConcierge",
        botAlias="$LATEST",
        userId="cloudClass",
        inputText= message
    )
    return {
        'statusCode': 200,
        'body': response["message"]
    }
