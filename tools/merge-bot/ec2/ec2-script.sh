#!/usr/bin/env bash
sudo su
yum install git
pip install PyGithub
pip install boto3
git clone https://gitlab.com/Rusllan/odoo-devops.git
chmod +x odoo-devops/tools/merge-bot/ec2/ec2-run.py
chmod +x odoo-devops/tools/merge-bot/merge-bot.py
chmod +x odoo-devops/tools/merge-bot/review-bot.py
python odoo-devops/tools/merge-bot/ec2/ec2-run.py
echo "*/5 * * * * python odoo-devops/tools/merge-bot/ec2/ec2-run.py" >> mycron
echo "@reboot python odoo-devops/tools/merge-bot/ec2/ec2-run.py" >> mycron
crontab mycron
rm mycron
