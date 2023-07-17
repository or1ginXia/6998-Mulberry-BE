import logging
import random
import string

from services import aws_service

logger = logging.getLogger()
logger.setLevel(logging.INFO)

FRONTEND_BASE_URL = 'https://d0ch1hik23.execute-api.us-east-1.amazonaws.com/v1'
CACHE_DYNAMO_NAME = 'cache'


def verification_link_generator(email: str) -> str or None:
    cache = aws_service.dynamo_client_factory(CACHE_DYNAMO_NAME)
    verification_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    cache.put_item(Item={'key': verification_code, 'email': email, 'purpose': 'email_verification'})

    return FRONTEND_BASE_URL + '/user/verify/' + verification_code


def verification_code_verifier(code: str) -> str or None:
    cache = aws_service.dynamo_client_factory(CACHE_DYNAMO_NAME)
    res = cache.get_item(Key={'key': code}).get('Item')
    if res is not None:
        res = res.get('email')
        # delete all codes generated for this email
        response = cache.scan(
            FilterExpression='#email = :email AND #purpose = :purpose',
            ExpressionAttributeNames={'#email': 'email', '#purpose': 'purpose'},
            ExpressionAttributeValues={':email': res, ':purpose': 'email_verification'}
        )

        # Loop through the matching items and delete them
        with cache.batch_writer() as batch:
            for item in response['Items']:
                batch.delete_item(Key={'key': item['key']})

    return res


def verification_email_sender(email: str) -> bool:
    ses_success = False
    verification_link = verification_link_generator(email)
    if verification_link is not None:
        ses_success = aws_service.ses_send_email(
            target_email_address=email,
            subject='Welcome to Mulberry! Please verify your email!',
            body='Hi<br><br>Welcome to Mulberry!<br><br>' +
                 'Please click this link to verify your email: ' +
                 '<a href="' + verification_link + '" target="_blank">' + verification_link + '</a><br>' +
                 'Your verification link will expire in 30 minutes.<br><br><br>Cheers,<br>Mulberry'
        )
    if not ses_success:
        logger.error('Email sent to %s failed!', email)
        return False

    return True
