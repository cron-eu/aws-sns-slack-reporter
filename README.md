aws-sns-slack-reporter
====

Abstract
----

This provides a lambda script which subscribes to an existing SNS Queue and send incoming messages to Slack.

The Setup can be done via CloudFormation, a publicly accessible CloudFormation Template is also provided.

### New in v1.1.0+

All alarms in the ALARM state will also be reported **on a scheduled basis** (defaults every 30 minutes,
configurable).


Setup
----

Create a new Slack Custom Integration and use the Slack Webhook URL to create the cloudformation stack:

```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/XXX/XXX
SNS_TOPIC=Default_CloudWatch_Alarms_Topic

aws cloudformation create-stack --stack-name sns-slack-handler \
  --template-url https://cron-aws-sns-slack-reporter.s3.eu-central-1.amazonaws.com/sns-slack-handler.yml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
  ParameterKey=StackWebhookURL,ParameterValue="${SLACK_WEBHOOK_URL}" ParameterKey=SNSTopic,ParameterValue="${SNS_TOPIC}"
```

To update the existing stack (to update the lambda to the latest version), do:

```bash
aws cloudformation update-stack --stack-name sns-slack-handler \
  --template-url https://cron-aws-sns-slack-reporter.s3.eu-central-1.amazonaws.com/sns-slack-handler.yml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
  ParameterKey=StackWebhookURL,UsePreviousValue=true ParameterKey=SNSTopic,UsePreviousValue=true
```

### Advanced Configuration

To change the default Slack Message Prefix, used when posting an alarm in ALARM state, use the Parameter `SlackAlarmPrefix`
when creating/updating the stack:

```shell
  --parameters \
  (..)
  ParameterKey=SlackAlarmPrefix,ParameterValue="@channel"
```

To tweak the time interval used to re-send notifications for alarms in the ALARM state, use the `AlertRate` parameter.

```shell
  --parameters \
  (..)
  ParameterKey=AlertRate,ParameterValue="rate (2 hours)"
```

Termination
----

To remove the stack and cleanup all resources, do:

```bash
aws cloudformation delete-stack --stack-name sns-slack-handler
aws cloudformation wait stack-delete-complete --stack-name sns-slack-handler
``` 


Author
----

* Remus Lazar <rl@cron.eu>
