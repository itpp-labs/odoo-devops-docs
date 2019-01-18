===============================
 GitHub Integration with IFTTT
===============================

Trigger Travis Success / Failure
================================

Prepare IFTTT's hooks
---------------------

* Log in / Sign up at https://ifttt.com/
* Click on ``Documentation`` button here: https://ifttt.com/maker_webhooks
* Replace ``{event}`` with event name, for example ``travis-success``. Do the same for another event, for exampe ``travis-failed``. Save the links you got. 

Create AWS Lambda function
--------------------------

`Create lambda function <https://console.aws.amazon.com/lambda/>`__ with following settings:

* Runtime

  Use ``Python 2.7``

* Environment variables

  * ``GITHUB_TOKEN`` -- generate one in https://github.com/settings/tokens . No settings are needed for public repositories
  * ``IFTTT_HOOK_GREEN``, ``IFTTT_HOOK_RED`` -- use IFTTT's hooks
  * ``LOG_LEVEL`` -- optional. Set to ``DEBUG`` to get detailed logs in AWS CloudWatch: https://console.aws.amazon.com/cloudwatch

* Trigger

  Use ``API Gateway``. Once you configure it and save, you will see ``Invoke URL`` under Api Gateway **details** section.

  Now register the URL as webhook at github: https://developer.github.com/webhooks/creating/.
  Use following webhook settings:

  * **Payload URL** -- the URL
  * **Content Type**: application/json
  * **Which events would you like to trigger this webhook?** -- *Let me select individual events* and then select ``[x] Check runs``

* Function Code

  Copy-paste this code: https://gitlab.com/itpp/odoo-devops/raw/master/tools/github-ifttt/lambda_function.py

Create IFTTT applets
--------------------

* **If** -- Service *Webhooks*
* **Then** -- whatever you like. For actions with text ingredients use following:

  * ``Value1`` -- Author of the pull-request
  * ``Value2`` -- Link to pull-request
  * ``Value3`` -- Link to the travis check
