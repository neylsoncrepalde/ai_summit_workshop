import uuid
import boto3

s3_client = boto3.client('s3')
dynamodb = boto3.client('dynamodb')
sns = boto3.client('sns')
TABLE_NAME = "competency-cases"
SNS_TOPIC = 'competency-notifications'

def get_named_parameter(event, name):
    return next(item for item in event['parameters'] if item['name'] == name)['value']

def get_named_property(event, name):
    return next(item for item in event['requestBody']['content']['application/json']['properties'] if item['name'] == name)['value']

def generateCase(event):
    # Extract parameters
    client = get_named_parameter(event, 'client') 
    casename = get_named_parameter(event, 'casename')
    challenge = get_named_parameter(event, 'challenge')
    solution = get_named_parameter(event, 'solution')
    budget = float(get_named_parameter(event, 'budget'))
    kpi = get_named_parameter(event, 'kpi')

    # Generate unique ID
    unique_id = uuid.uuid1().int>>64

    # Save sheet information on Dynamo Table
    dynamodb.put_item(
        TableName=TABLE_NAME,
        Item={
            'caseId': {
                'N': str(unique_id),
            },
            'client': {
                'S': client,
            },
            'casename': {
                'S': casename,
            },
            'challenge': {
                'S': challenge,
            },
            'solution': {
                'S': solution,
            },
            'budget': {
                'N': str(budget),
            },
            'kpi': {
                'S': kpi,
            }
        }
    )
    # Return response matching schema
    return {
        "id": str(unique_id),
        "client": client,
        "casename": casename,
        "challenge": challenge,
        "solution": solution,
        "budget": budget,
        "kpi": kpi
    }

def checkCase(event):
    # Extract parameter
    caseId = get_named_parameter(event, 'caseId')
    # Get information from Dynamo Table
    info = dynamodb.get_item(
        TableName=TABLE_NAME,
        Key={
            'caseId': {
                'N': str(caseId),
            }
        }
    )
    client = info['Item']['client']['S']
    casename = info['Item']['casename']['S']
    challenge = info['Item']['challenge']['S']
    solution = info['Item']['solution']['S']
    budget = info['Item']['budget']['N']
    kpi = info['Item']['kpi']['S']

    # Return success response
    return {
        "id": str(caseId),
        "client": client,
        "casename": casename,
        "challenge": challenge,
        "solution": solution,
        "budget": budget,
        "kpi": kpi
    }


def notify(event):
    # Extract parameter
    info_dict = checkCase(event)
    sns.publish(
        TopicArn=SNS_TOPIC,
        Message=f"New case registered: {info_dict}",
        Subject="New Competency Case"
    )
    return True


def lambda_handler(event, context):

    response_code = 200
    action_group = event['actionGroup']
    api_path = event['apiPath']

    if api_path == '/generateCase':
        result = generateCase(event)
    elif api_path == '/checkCase':
        result = checkCase(event)
    elif api_path == '/notify':
        result = notify(event)
    else:
        response_code = 404
        result = f"Unrecognized api path: {action_group}::{api_path}"

    response_body = {
        'application/json': {
            'body': result 
        }
    }

    action_response = {
        'actionGroup': event['actionGroup'],
        'apiPath': event['apiPath'],
        'httpMethod': event['httpMethod'],
        'httpStatusCode': response_code,
        'responseBody': response_body
    }

    api_response = {'messageVersion': '1.0', 'response': action_response}
    return api_response
