#!/usr/bin/env bash
sudo yum install git
pip install PyGithub
pip install boto3
git clone https://gitlab.com/Rusllan/odoo-devops.git
sudo chmod +x odoo-devops/tools/merge-bot/ec2/ec2-run.py
sudo chmod +x odoo-devops/tools/merge-bot/merge-bot.py
sudo chmod +x odoo-devops/tools/merge-bot/review-bot.py
python odoo-devops/tools/merge-bot/ec2/ec2-run.py
echo "*/5 * * * * /usr/bin/python /home/ec2-user/odoo-devops/tools/merge-bot/ec2/ec2-run.py" >> mycron
echo "@reboot /usr/bin/python /home/ec2-user/odoo-devops/tools/merge-bot/ec2/ec2-run.py" >> mycron
crontab mycron
rm mycron
