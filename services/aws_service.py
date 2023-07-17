import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamo_tables = {
    "user": "mulberry-user",
    "activity": "mulberry-activity",
    "coupon": "mulberry-coupon",
    "match": "mulberry-match",
    "message": "mulberry-message",
    "cache": "mulberry-cache"
}


def dynamo_client_factory(table: str):
    db = boto3.resource('dynamodb')
    db_table = dynamo_tables.get(table)
    if db_table is None:
        logger.error("No DynamoDB Table - %s", table)
        raise RuntimeError("Can't create dynamo db client")
    return db.Table(db_table)


def ses_send_email(target_email_address: str,
                   subject: str, body: str) -> bool:
    ses_client = boto3.client('ses')
    message = {
        'Subject': {'Data': subject},
        'Body': {'Html': {'Data': body}}
    }
    try:
        ses_client.send_email(
            Source=target_email_address,
            Destination={'ToAddresses': [target_email_address]},
            Message=message
        )
        logger.info("Email send successfully: target - %s, body - %s",
                    target_email_address, body)
        return True
    except Exception as e:
        logger.error("Failed to send email: target - %s, body - %s",
                     target_email_address, body)
        logger.exception(e)
        return False
