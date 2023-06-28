import os
from requests.structures import CaseInsensitiveDict
from datetime import datetime, timedelta

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.utilities.data_classes import event_source, EventBridgeEvent


from .datastore.wbgt import (
    DynamoDBWBGTRepository,
)
from .service.wbgt import (
    WBGTService
)
from .app.import_wbgt import (
    WBGTImporterApplication
)
from .lib.wbgt_data import WBGTData

logger = Logger()


def import_wbgt():
    wbgt_table_name = os.environ.get("TABLE_WBGT")
    if wbgt_table_name is None:
        raise Exception("Please set TABLE_WBGT env")

    wbgt_repo = DynamoDBWBGTRepository(wbgt_table_name)
    wbgt_svc = WBGTService()
    wbgt_data_lib = WBGTData()

    # load wbgt points
    wbgt_importer = WBGTImporterApplication(wbgt_repo, wbgt_svc, wbgt_data_lib)
    wbgt_importer.load_wbgt_pred_data()


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.LAMBDA_FUNCTION_URL)
@event_source(data_class=EventBridgeEvent)
def lambda_handler(event: EventBridgeEvent, context: LambdaContext):
    logger.info(event)
    import_wbgt()
