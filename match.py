import json
import logging

from services import aws_service

logger = logging.getLogger()
logger.setLevel(logging.INFO)

match_db = aws_service.dynamo_client_factory("match")

"""
Match Database Architecture
{
    'email': '1@1.1', 
    'today': ['2@2.2', '3@3.3']
}
'today' contains all the matching user emails for today.
"""


def make_new_match(email: str) -> list:
    """
    Matching Algorithm:
    1. opposite gender
    2. location match
    3. interest match

    A score will be computed to order the potential match users.
        The same location will gain 3 points;
        The same interest will gain 1 point;

    Only the top-10 potential matched users will be returned.
    """
    user_db = aws_service.dynamo_client_factory("user")
    user = user_db.get_item(Key={'email': email}).get('Item')
    expected_gender = 'female' if user['gender'] == 'male' else 'male'
    expected_location = user['location']
    expected_interest = [user['interest1'], user['interest2'], user['interest3']]

    potential_match = []
    users = user_db.scan()['Items']
    for user in users:
        if user['status'] != 'ACTIVE':
            continue

        # Filter out not matching gender
        if user['gender'] != expected_gender:
            continue

        score = 0
        if user['location'] == expected_location:
            score += 3
        if user['interest1'] in expected_interest:
            score += 1
        if user['interest2'] in expected_interest:
            score += 1
        if user['interest3'] in expected_interest:
            score += 1

        if score == 0:
            continue

        potential_match.append({'score': score, 'email': user['email']})

    potential_match = sorted(potential_match, key=lambda x: x['score'], reverse=True)
    return [item['email'] for item in potential_match[:10]]


def get_match(event: dict):
    logger.info("get_match")
    email = event['email']

    match_record = match_db.get_item(Key={'email': email}).get('Item')

    # This user has no previous match results
    if match_record is None or len(match_record['today']) == 0:
        match_record = {
            'email': email,
            'today': make_new_match(email)
        }
        match_db.put_item(Item=match_record)

    return {'status': 'success', 'data': match_record['today']}


function_register = {
    ('/match', 'GET'): get_match
}


def request_handler(_event):
    function = function_register[(_event['resource'], _event['httpMethod'])]
    return function(_event)
