#!/usr/bin/env python3

import os
import boto3.session
import json
import datetime
import urllib3
import dateutil.tz
import argparse
from dataclasses import dataclass

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


@dataclass
class Alarm:
    name: str
    description: str
    reason: str
    state: str
    state_change_time: datetime.datetime


def send_slack_alarm(alarm: Alarm, timestamp):
    """
    Send a given CloudWatch Alarm to Slack

    :return: None
    """

    berlin = dateutil.tz.gettz('Europe/Berlin')

    is_alarm = alarm.state == 'ALARM'

    send_slack_message({
        'attachments': [
            {
                'color': '#c00000' if is_alarm else '#00c000',
                'pretext': ("@here {}" if is_alarm else "{}").format(alarm.description),
                'title': alarm.state,
                'fields': [
                    {
                        'title': 'State Reason',
                        'value': alarm.reason,
                        'short': False,
                    },
                    {
                        'title': 'Alarm Name',
                        'value': alarm.name,
                        'short': True,
                    },
                    {
                        'title': 'State Change Time',
                        'value': alarm.state_change_time.astimezone(berlin).strftime("%a, %d %b %Y %H:%M:%S"),
                        'short': True,
                    },
                ],
                'footer': 'SNS Event',
                'ts': timestamp.timestamp(),
            }
        ]
    })


def process_message(sns):
    """
    Process a single SNS Event

    :param sns: ECS Event data
    :return: True if a notification was sent.
    """

    def get_utc_json_date(string):
        tz = dateutil.tz.gettz('Europe/Berlin')
        return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S.%fZ').astimezone(tz)

    timestamp = get_utc_json_date(sns['Timestamp'])
    message = json.loads(sns['Message'])

    def get_date(string):
        return datetime.datetime.strptime(string, '%Y-%m-%dT%H:%M:%S.%f%z')

    try:
        alarm = Alarm(name=message['AlarmName'],
                      description=message['AlarmDescription'],
                      reason=message['NewStateReason'],
                      state=message['NewStateValue'],
                      state_change_time=get_date(message['StateChangeTime']))

        send_slack_alarm(alarm, timestamp)

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


def get_alarms(process_all=False):
    """
    Gets all alarms from CloudWatch
    :return:
    """
    global session
    client = session.client('cloudwatch')
    response = client.describe_alarms()

    return [alarm for alarm in response['MetricAlarms'] if process_all or alarm['StateValue'] == 'ALARM']


def list_alarms(process_all=False):
    """
    List all available alarms with their state
    :return: None
    """

    def get_local_date_string(date):
        tz = dateutil.tz.gettz('Europe/Berlin')
        return date.astimezone(tz).strftime('%c')

    for alarm in get_alarms(process_all):
        print(f"{alarm['AlarmName']}: {alarm['StateValue']} ({get_local_date_string(alarm['StateUpdatedTimestamp'])})")


def send_notifications(process_all=False):
    """
    Send a notification to Slack which contains all alarms currently in an ALARM state
    :return:
    """
    for alarm in get_alarms(process_all):
        alarm = Alarm(name=alarm['AlarmName'],
                      description=alarm['AlarmDescription'],
                      reason=alarm['StateReason'],
                      state=alarm['StateValue'],
                      state_change_time=alarm['StateUpdatedTimestamp']
                      )
        send_slack_alarm(alarm, datetime.datetime.now())


def cli_handler():
    import sys
    process_message(json.loads(sys.stdin.read()))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='AWS SNS Slack Reporter')
    parser.add_argument('--list', help="List all available CloudWatch Alarms", action='store_true')
    parser.add_argument('--send', help="Send Alerts for all Alarms in ALARM state", action='store_true')
    parser.add_argument('--all', help="Process all alarms regardless of their state", action='store_true')

    args = parser.parse_args()

    # read in the .env file
    with open('.env', 'r') as fh:
        # noinspection PyTypeChecker
        vars_dict = dict(
            tuple(line.split('='))
            for line in fh.readlines() if not line.startswith('#')
        )
    print(vars_dict)
    os.environ.update(vars_dict)

    if args.list:
        list_alarms(args.all)
    elif args.send:
        send_notifications(args.all)
    else:
        cli_handler()
