from datetime import datetime, timedelta

import jwt

SECRET = 'secret'
TEST_USER_EMAIL = 'test-user-email'
TEST_USER_TOKEN = 'testusertoken'
ALGORITHM = 'HS256'
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
AUTHENTICATION_DISABLED_RESOURCES = [
    '/user/signup',
    '/user/login',
    '/user/verify/resend/{email}',
    '/user/verify/{token}'
]


def parseEmail(_event: dict) -> str:
    try:
        token = _event['headers']['Authorization']
    except (KeyError, TypeError):
        token = None

    if token is None:
        if _event['resource'] not in AUTHENTICATION_DISABLED_RESOURCES:
            raise Authentication401Exception
        return TEST_USER_EMAIL
    else:
        # For TEST_USER_TOKEN, use the 'email' field in query param
        if token == TEST_USER_TOKEN:
            try:
                return _event['queryStringParameters']['email']
            except (KeyError, TypeError):
                return TEST_USER_EMAIL

        # Decode the token
        try:
            decoded_token = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
            expired_date_time = datetime.strptime(
                decoded_token.get('expiredAt'),
                DATETIME_FORMAT)
        except Exception:
            raise Authentication403Exception

        # Check if token is expired
        if expired_date_time is None or expired_date_time < datetime.now():
            raise Authentication403Exception

        return decoded_token.get('email')


def generateJWTToken(email: str) -> str:
    return jwt.encode({
        'email': email,
        'expiredAt': (datetime.now() + timedelta(minutes=30)).strftime(DATETIME_FORMAT)
    }, SECRET, ALGORITHM)


class Authentication401Exception(Exception):
    """No token is present"""
    pass


class Authentication403Exception(Exception):
    """Token is invalid or expired"""
    pass
