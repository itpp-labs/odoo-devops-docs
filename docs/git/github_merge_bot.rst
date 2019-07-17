======================
 Merge bot for GitHub
======================

The script gives the right to a certain circle of people to merge branches in the repository by sending the certain comment in the pull request.

Prepare IFTTT's hooks
---------------------

* Log in / Sign up at https://ifttt.com/
* Click on ``Documentation`` button here: https://ifttt.com/maker_webhooks
* Replace ``{event}`` with event name, for example ``travis-not-finished-pr``, ``travis-success-pr`` and ``travis-failed-pr``. Save the links you got.

Create AWS Lambda function
--------------------------

`Create lambda function <https://console.aws.amazon.com/lambda/>`__ with following settings:

* Runtime

  Use ``Python 3.6``

* Environment variables

  * ``GITHUB_TOKEN`` -- generate one in https://github.com/settings/tokens . Select scope ``repo``.
  * ``USERNAMES`` -- use comma-separated list of Github's usernames without @.
  * ``LOG_LEVEL`` -- optional. Set to DEBUG to get detailed logs in AWS CloudWatch.
  * ``MSG_RQST_MERGE`` -- message-request for merge. Default: ``I approve to merge it now``
  * ``IFTTT_HOOK_RED_PR``, ``IFTTT_HOOK_GREEN_PR``, ``IFTTT_HOOK_NOT_FINISHED_PR`` -- use IFTTT's hooks

* Trigger

  Use ``API Gateway``. Once you configure it and save, you will see ``API endpoint`` under Api Gateway **details** section. Use option ``Open``

  Now register the URL as webhook at github: https://developer.github.com/webhooks/creating/.
  Use following webhook settings:

  * **Payload URL** -- the URL
  * **Content Type**: application/json
  * **Which events would you like to trigger this webhook?** -- *Let me select individual events* and then select ``[x] Issue comments``

* Function Code

  * Copy-paste this code: https://gitlab.com/itpp/odoo-devops/raw/master/tools/github-merge-bot/lambda_function.py

Create IFTTT applets
--------------------

* **If** -- Service *Webhooks*.

  Use ``{event}`` from ``Prepare IFTTT's hooks`` of this instruction. For example: ``Event Name`` = ``travis-not-finished-pr``, ``Event Name`` = ``travis-failed-pr``.

* **Then** -- whatever you like. For actions with text ingredients use following for failed, success and not finished checks:

  * ``Value1`` -- Author of the pull-request
  * ``Value2`` -- Link to pull-request
  * ``Value3`` -- Message about it

Logs
----

* AWS CloudWatch: https://console.aws.amazon.com/cloudwatch . Choice tab ``Logs``
* IFTTT logs: https://ifttt.com/activity


