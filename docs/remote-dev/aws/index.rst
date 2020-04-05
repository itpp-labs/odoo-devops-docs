===================================
 Remote development on EC2 servers
===================================

EC2 server with EBS is a good option for remote development, because you can
stop server and don't pay for CPU and RAM when you don't work on the server.

To simplify starting and stopping the server, you can deploy telegram bot as
described below.


.. contents::
   :local:

Control commands
================


* /up -- turn on server or extend time to shutdown

  In response it sends:
  * IP
  * Hostname
  * Time to automatic shutdown
  * Text: *To shutdown earlier send /shutdown or
    schedule message "Shutdown"

* /shutdown -- turn the server off after confirmation
* Shutdown -- turn the server off without confirmation


Settings
========

On creating AWS Lambda, you would need to set following Environment variables:

* TELEGRAM_TOKEN=<telegram token you got from Bot Father>
* DOMAIN="USERCODE.example.com"
* DOMAIN_NO_SSL="USERCODE.nossl.example.com"
* USER_123_SERVER=*<Server-ARN>*, USER_123_CODE=*some-user-code*

  * 123 is a telegram user ID. You can get one via `Get My ID bot <https://telegram.me/itpp_myid_bot>`__
* AUTO_SHUTDOWN=*<time in minutes before server will be shutdown>*
* LOG_LEVEL=<LEVEL> -- ``DEBUG``, ``INFO``, etc.

Bot source
==========

See https://github.com/itpp-labs/odoo-devops-docs/blob/master/tools/ec2-dev-bot/lambda_function.py

Deployment
==========

Create a bot
------------

https://telegram.me/botfather -- follow instruction to set bot name and get bot token

Create EC2 server
-----------------

You need a server per each user. We recommend using burstable server, e.g. `EC2
T3 instances <https://aws.amazon.com/ru/ec2/instance-types/t3/>`__.

Prepare zip file
----------------

To make a `deployment package <https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html>`_ execute following commands::

    mkdir /tmp/bot
    cd /tmp/bot

    pip3 install python-telegram-bot pynamodb -t .
    wget https://raw.githubusercontent.com/itpp-labs/odoo-devops-docs/master/tools/ec2-dev-bot/lambda_function.py -O lambda_function.py
    zip -r /tmp/bot.zip *

Create Lambda function
---------------------- 

* Navigate to https://console.aws.amazon.com/lambda/home
* Click *Create function*
* Configure the function as described below

Runtime
~~~~~~~

In *AWS: Lambda service*

Use ``Python 3.7``

Trigger
~~~~~~~

In *AWS: Lambda service*

* **API Gateway**. Once you configure it and save, you will see ``Invoke URL`` under Api Gateway **details** section
* **CloudWatch Events**. Create new rule for reminders, for example set

  * *Rule name* -- ``ec2-dev-bot-cron``
  * *Schedule expression* -- ``rate(1 hour)``


Role
~~~~

In *AWS: IAM (Identity and Access Management) service: Policies*

* Create policy of actions for DynamoDB:
  
  * *Service* -- ``DynamoDB``
  * *Action* -- ``All DynamoDB actions``
  * *Resources* -- ``All Resources``

In *AWS: IAM service: Roles*

In list of roles choose the role, which was named in process of creating lambda function, and attach to it recently created policy for DynamoDB


Timeout
~~~~~~~

in *AWS: Lambda service*

Execution time depends on telegram server and amount of requests there. So, think about 30 seconds for limit.


Register webhook at telegram
----------------------------

.. code-block:: sh

    AWS_API_GATEWAY=XXX
    TELEGRAM_TOKEN=XXX
    curl -XPOST https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook --data "url=$AWS_API_GATEWAY" --data "allowed_updates=['message','callback_query']"
