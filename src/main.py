#!/usr/bin/env python3

import argparse
import os
import boto3.session
import json
import datetime
import urllib3
import dateutil.tz

import pprint

http = urllib3.PoolManager()

# noinspection PyTypeChecker
session = boto3.Session()


def process_event(data, process_all=False):
    """
    Process a single ECS Event

    :param data: ECS Event data
    :param process_all: Process all events, not only non-zero exit level ones which is the default.
    :return: True if a notification was sent.
    """

    pprint.pprint(data)

    def get_json_date(string):
        tz = dateutil.tz.gettz('Europe/Berlin')
        return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S.%fZ').astimezone(tz)


    is_alarm = True
    pretext = 'My Pretext'

    send_slack_message({
        'attachments': [
            {
                'color': '#00c000' if is_alarm else '#c00000',
                'pretext': ("{}" if is_alarm else "@here {}").format(pretext),
                'title': "My Title",
                'footer': 'SNS Event',
            }
        ]
    })
    return True


def send_slack_message(payload):
    """

    :param payload: Payload to be sent to the Slack Webhook
    :return: Slack Webhook API Response
    """
    slack_web_hook_url = os.environ['SLACK_WEBHOOK_URL']

    return http.request('POST', slack_web_hook_url, body=json.dumps(payload).encode('utf-8'))


# noinspection PyUnusedLocal
def lambda_handler(event, context):
    global session
    processed = process_event(event, True)

    return {
        'message': 'Slack Notification was sent successfully.' if processed else 'No Slack Notification was sent.'
    }


def cli_handler():
    parser = argparse.ArgumentParser(description='SNS Handler. Pipe the JSON event data via standard input')
    args = parser.parse_args()

    import sys
    process_event(json.loads(sys.stdin.read()), args.all)


if __name__ == '__main__':
    # read in the .env file
    with open('.env', 'r') as fh:
        # noinspection PyTypeChecker
        vars_dict = dict(
            tuple(line.split('='))
            for line in fh.readlines() if not line.startswith('#')
        )
    print(vars_dict)
    os.environ.update(vars_dict)
    cli_handler()
