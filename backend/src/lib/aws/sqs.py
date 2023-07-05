import boto3
import botocore.exceptions
from boto3.dynamodb.conditions import Key
from typing import List, Optional
import json
from decimal import Decimal


####################################
# SQS #
####################################

def send_queue_message(queue_name: str, message: str):
    sqs = boto3.resource('sqs')
    queue = sqs.get_queue_by_name(QueueName=queue_name)

    try:
        queue.send_message(
            MessageBody=message,
        )
    except botocore.exceptions.ClientError:
        raise
