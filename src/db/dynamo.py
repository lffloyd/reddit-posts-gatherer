import os
import boto3
import math
from datetime import datetime

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
SIMPLE_DATE_FORMAT = '%Y-%m-%d'

if os.getenv('AWS_SAM_LOCAL') == 'true':
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://localhost:8000')
else:
    dynamodb = boto3.resource('dynamodb')

table = dynamodb.Table(os.getenv('LAST_SEARCHED_DATE_TABLE'))


def get_last_searched_date():
    default_date = datetime.strptime(os.getenv('START_DATE'), SIMPLE_DATE_FORMAT)

    try:
        response = table.get_item(
            Key = { 'id': os.getenv('LANGUAGE') }
        )
        item = response['Item']
        print(f'Item found: {item}')
        if item != None:
            db_date = datetime.strptime(item['last_searched_date'], DATE_FORMAT)
            timestamp = math.ceil(db_date.timestamp()) + 1
            return datetime.fromtimestamp(timestamp)

        return default_date
    except Exception as e:
        print(f'Error while retrieving date from Dynamo: {e}')
        return default_date


def save_last_searched_date(last_searched_date):
    try:
        date_string = last_searched_date.strftime(DATE_FORMAT)
        response = table.put_item(
            Item = {
                'id': os.getenv('LANGUAGE'),
                'last_searched_date': date_string,
            }
        )

        print(f'Put response: {response}')
        return None
    except Exception as e:
        print(f'Error while saving date {last_searched_date} on Dynamo: {e}')
        raise e
