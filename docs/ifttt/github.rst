===============================
 GitHub Integration with IFTTT
===============================

Trigger Travis Success / Failure
================================

Prepare IFTTT's hooks
---------------------

* Log in / Sign up at https://ifttt.com/
* Click on ``Documentation`` button here: https://ifttt.com/maker_webhooks
* Replace ``{event}`` with event name, for example ``travis-success-pr``. Do the same for another event, for example ``travis-failed-pr`` and ``travis-failed-branch``. Save the links you got. 

Create AWS Lambda function
--------------------------

`Create lambda function <https://console.aws.amazon.com/lambda/>`__ with following settings:

* Runtime

  Use ``Python 2.7``

* Environment variables

  * ``GITHUB_TOKEN`` -- generate one in https://github.com/settings/tokens . No settings are needed for public repositories.
  * ``IFTTT_HOOK_GREEN_PR``, ``IFTTT_HOOK_RED_PR``, ``IFTTT_HOOK_RED_BRANCH`` -- use IFTTT's hooks
  * ``LOG_LEVEL`` -- optional. Set to ``DEBUG`` to get detailed logs in AWS CloudWatch.

* Trigger

  Use ``API Gateway``. Once you configure it and save, you will see ``API endpoint`` under Api Gateway **details** section. Use option ``Open``

  Now register the URL as webhook at github: https://developer.github.com/webhooks/creating/.
  Use following webhook settings:

  * **Payload URL** -- the URL
  * **Content Type**: application/json
  * **Which events would you like to trigger this webhook?** -- *Let me select individual events* and then select ``[x] Check runs``

* Function Code

  * Copy-paste this code: https://gitlab.com/itpp/odoo-devops/raw/master/tools/github-ifttt/lambda_function.py
  
Create IFTTT applets
--------------------

* **If** -- Service *Webhooks*
Use ``{event}`` from ``Prepare IFTTT's hooks`` of this instruction. For example: ``Event Name`` = ``travis-success-pr``, ``Event Name`` = ``travis-failed-pr`` and ``Event Name`` = ``travis-failed-branch``

* **Then** -- whatever you like. For actions with text ingredients use following:

  * ``Value1`` -- Author of the pull-request
  * ``Value2`` -- Link to pull-request
  * ``Value3`` -- Link to the travis check

Travis settings
---------------

* Update ``.travis.yml`` to get a notification in lambda when travis check is finished. You can configure either always notify on failure or only when previous check was successful. Check Travis Documentation for details: https://docs.travis-ci.com/user/notifications/#configuring-webhook-notifications
* Look it for example:
.. code-block:: python

    notifications:
        webhooks: 
            on_failure: change 
        urls:
          - "https://9ltrkrik2l.execute-api.eu-central-1.amazonaws.com/default/TriggerTravis/" 
          
Logs
----

* AWS CloudWatch: https://console.aws.amazon.com/cloudwatch . Choice tab ``Logs``
* IFTTT logs: https://ifttt.com/activity


