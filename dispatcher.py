from services.authentication_service import *

import json
import logging
import importlib

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def request_dispatcher(event, context):
    logger.info('-------------------------')
    logger.info(event)

    try:
        # validate the input token and parse the user email
        event['email'] = parseEmail(event)

        # find the proper module and pass the request to the request handler
        module_name = None
        try:
            # parse the module_name based on resource
            module_name = event['resource'].split("/")[1]
            if module_name is None:
                raise ModuleNotFoundError
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            logger.error("Can't find proper request handler: resource - %s, module - %s",
                         event['resource'], module_name)
            return {
                'statusCode': 400,
                'headers': {
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': '*'
                },
                'body': '{"status": "fail", "message":"No proper handler found for the endpoint"}'
            }

        handler = module.request_handler
        resp = handler(event)

        logger.info('Complete request')
        logger.info(resp)
        logger.info('-------------------------')
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': json.dumps(resp)
        }
    except Authentication401Exception:
        logger.error("No token is present")
        return {
            'statusCode': 401,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': '{"status": "fail", "message":"No token is present"}'
        }
    except Authentication403Exception:
        logger.error("Token is invalid or expires")
        return {
            'statusCode': 403,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': '{"status": "fail", "message":"Token is invalid or expires"}'
        }
    except Exception as e:
        logger.error("Unhandled Exception occurs!")
        logger.exception(e)
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': '*'
            },
            'body': '{"status": "fail", "message":"Unhandled Exception occurs"}'
        }
    finally:
        logger.info('-------------------------')
