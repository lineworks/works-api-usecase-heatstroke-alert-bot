from ..lib.aws import sqs


class SQSMessagePublisher():
    def __init__(self, queue_name: str):
        self.queue_name = queue_name

    def publish(self, message: str):
        sqs.send_queue_message(self.queue_name, message)
