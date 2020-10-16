#!/usr/bin/env python3

import os
import boto3.session
import json
import datetime
import urllib3
import dateutil.tz

http = urllib3.PoolManager()

# noinspection PyTypeChecker
session = boto3.Session()


def process_event(data):
    """
    Process the full SNS Queue Subscription Payload

    :param data: payload
    :return: True if at least one message has been processed successfully
    """

    success = False

    for record in data['Records']:
        sns = record['Sns']
        if process_message(sns):
            success = True

    return success


def process_message(sns):
    """
    Process a single SNS Event

    :param sns: ECS Event data
    :return: True if a notification was sent.
    """

    def get_utc_json_date(string):
        tz = dateutil.tz.gettz('Europe/Berlin')
        return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S.%fZ').astimezone(tz)

    def get_date_with_tz(string):
        return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S.%f%z')

    timestamp = get_utc_json_date(sns['Timestamp'])
    message = json.loads(sns['Message'])

    try:
        alarm_name = message['AlarmName']
        alarm_description = message['AlarmDescription']

        state = message['NewStateValue']
        state_reason = message['NewStateReason']

        state_change_time = get_date_with_tz(message['StateChangeTime'])

        is_alarm = state == 'ALARM'

        send_slack_message({
            'attachments': [
                {
                    'color': '#00c000' if is_alarm else '#c00000',
                    'pretext': ("{}" if is_alarm else "@here {}").format(state),
                    'title': alarm_name,
                    'fields': [
                        {
                            'title': 'Alarm Description',
                            'value': alarm_description,
                            'short': False,
                        },
                        {
                            'title': 'State Reason',
                            'value': state_reason,
                            'short': False,
                        },
                        {
                            'title': 'State Change Time',
                            'value': state_change_time.strftime("%a, %d %b %Y %H:%M:%S"),
                            'short': True,
                        }
                    ],
                    'footer': 'SNS Event',
                    'ts': timestamp.timestamp(),
                }
            ]
        })

    except KeyError:
        print('ERROR: invalid message payload format: {}'.format(json.dumps(message)))
        pass

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
    processed = process_event(event)

    return {
        'message': 'Slack Notification was sent successfully.' if processed else 'No Slack Notification was sent.'
    }


def cli_handler():
    import sys
    process_message(json.loads(sys.stdin.read()))


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
