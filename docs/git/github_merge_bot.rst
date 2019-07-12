======================
 Merge bot for GitHub
======================

The script gives the right to a certain circle of people to merge branches in the repository by sending the certain comment in the pull request.

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

* Trigger

  Use ``API Gateway``. Once you configure it and save, you will see ``API endpoint`` under Api Gateway **details** section. Use option ``Open``

  Now register the URL as webhook at github: https://developer.github.com/webhooks/creating/.
  Use following webhook settings:

  * **Payload URL** -- the URL
  * **Content Type**: application/json
  * **Which events would you like to trigger this webhook?** -- *Let me select individual events* and then select ``[x] Issue comments``

* Function Code

  * Copy-paste this code: https://gitlab.com/itpp/odoo-devops/raw/master/tools/github-merge-bot/lambda_function.py

* Logs

  AWS CloudWatch: https://console.aws.amazon.com/cloudwatch . Choice tab ``Logs``



