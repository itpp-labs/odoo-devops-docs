=====================================
 Remote development on EC2 instances
=====================================

EC2 instance with EBS is a good option for remote development, because you can
stop instance and don't pay for CPU and RAM when you don't work on the instance.

To simplify starting and stopping the instance, you can deploy telegram bot as
described below.


.. contents::
   :local:

Roadmap
=======

* Schedule is not supported yet
* Domains are not supported yet

Control commands
================


* /up -- turn on instance or extend time to shutdown

  In response it sends:

  * IP
  * Hostname
  * Time to automatic shutdown
  * Text: *To shutdown earlier send /shutdown or
    schedule message "Shutdown"

* /status -- get instance info
* /shutdown -- turn the instance off after confirmation
* Shutdown -- turn the instance off without confirmation


Settings
========

On creating AWS Lambda, you would need to set following Environment variables:

* TELEGRAM_TOKEN=<telegram token you got from Bot Father>
* DOMAIN="USERCODE.example.com"
* DOMAIN_NO_SSL="USERCODE.nossl.example.com"
* USER_123_INSTANCE=*<Instance ID>*, USER_123_CODE=*some-user-code*

  * 123 is a telegram user ID. You can get one via `Get My ID bot <https://telegram.me/itpp_myid_bot>`__
  * *Instance ID* looks like ``i-07e6...`` and can be found in Description tab of existing Instance
* AUTO_SHUTDOWN=*<time in minutes before instance will be shutdown>*
* AUTO_SHUTDOWN_WARNING=*<time in minutes for warning before actual shutdown>*
* LOG_LEVEL=<LEVEL> -- ``DEBUG``, ``INFO``, etc.

Bot source
==========

See https://github.com/itpp-labs/odoo-devops-docs/blob/master/tools/ec2-dev-bot/lambda_function.py

Deployment
==========

Create a bot
------------

https://telegram.me/botfather -- follow instruction to set bot name and get bot token

Create EC2 instance
-------------------

You need a instance per each user. We recommend using burstable instance, e.g. `EC2
T3 instances <https://aws.amazon.com/ru/ec2/instance-types/t3/>`__.

Prepare zip file
----------------

To make a `deployment package <https://docs.aws.amazon.com/lambda/latest/dg/lambda-python-how-to-create-deployment-package.html>`_ execute following commands::

    mkdir /tmp/bot
    cd /tmp/bot

    pip3 install python-telegram-bot pynamodb --system -t .
    wget https://raw.githubusercontent.com/itpp-labs/odoo-devops-docs/master/tools/ec2-dev-bot/lambda_function.py -O lambda_function.py
    # delete built-in or unused dependencies
    rm -rf botocore* tornado* docutils*
    zip -r /tmp/bot.zip *

Create Lambda function
---------------------- 

* Navigate to https://console.aws.amazon.com/lambda/home
* Click *Create function*
* Configure the function as described below

Runtime
~~~~~~~

In *AWS: Lambda service*

Use ``Python 3.8``

Permissions (Role)
~~~~~~~~~~~~~~~~~~

In *AWS: IAM service: Policies*

* Create policy of actions for DynamoDB:
  
  * *Service* -- ``DynamoDB``
  * *Action* -- ``All DynamoDB actions``
  * *Resources* -- ``All Resources``

* Create policy of actions for EC2:
  
  * *Service* -- ``EC2``
  * *Action* -- ``All EC2 actions``
  * *Resources* -- ``All Resources``

In *AWS: IAM service: Roles*

* Open role attached to the lambda function
* Attache created policies

Function code
~~~~~~~~~~~~~

* ``Code entry type``: *Upload a .zip file*
* Upload ``bot.zip``

Timeout
~~~~~~~

in *AWS: Lambda service*

Execution time depends on telegram server, instance start/stop time. So, think about at least 35 seconds  for limit. For your information, to checking instance status happens every 15 secods, so it's good idea to set limit to mulitple of 15 plus few seconds.

Trigger
~~~~~~~

In *AWS: Lambda service*

* **API Gateway**. Once you configure it and save, you will see ``Invoke URL`` under Api Gateway **details** section
* **CloudWatch Events**. Create new rule for reminders, for example set

  * *Rule name* -- ``ec2-dev-bot-cron``
  * *Schedule expression* -- ``rate(1 hour)``

Register webhook at telegram
----------------------------

.. code-block:: sh

    AWS_API_GATEWAY=XXX
    TELEGRAM_TOKEN=XXX
    curl -XPOST https://api.telegram.org/bot$TELEGRAM_TOKEN/setWebhook --data "url=$AWS_API_GATEWAY" --data "allowed_updates=['message','callback_query']"
