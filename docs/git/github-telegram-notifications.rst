=================================
 Notifications to Telegram Group
=================================

In this example we make a bot, that will send notifications to telegram group on
new issues. You can slightly change the script to use other type of events.

Telegram Bot
============

* In telegram client open `BotFather <https://t.me/botfather>`__
* Send /newbot command to create a new bot
* Follow instruction to set bot name and get bot token
* Keep your token secure and store safely, it can be used by anyone to control your bot

Telegram Group
==============

Add created bot to the group, where it will send notifications

You will need Group ID. To get one, temporarly add `Get My ID <https://telegram.me/itpp_myid_bot>`__ bot to the group.

Secrets
=======

Add following `secrets <https://help.github.com/en/articles/virtual-environments-for-github-actions#creating-and-using-secrets-encrypted-variables>`__

* ``TELEGRAM_TOKEN`` -- bot token
* ``TELEGRAM_CHAT_ID`` -- Group ID. Normally, it's negative integer

Github Actions
==============

Create ``.github/workflows/main.yml`` file (you can also use ``[Set up a workflow yourself]`` button at ``Actions`` tab of the repository page)

.. code-block:: yaml

    name: Telegram Notifications

    on:
      issues:
        types: [opened, reopened, deleted, closed]

    jobs:
      notify:

        runs-on: ubuntu-latest

        steps:
        - name: Send notifications to Telegram
          run: curl -s -X POST https://api.telegram.org/bot${{ secrets.TELEGRAM_TOKEN }}/sendMessage -d chat_id=${{ secrets.TELEGRAM_CHAT_ID }} -d text="${MESSAGE}" >> /dev/null
          env:
            MESSAGE: "Issue ${{ github.event.action }}: \n${{ github.event.issue.html_url }}"

Try it out
==========

* Create new issue
* RESULT: bot sends a notification
