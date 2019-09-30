#!/bin/bash
sudo yum install git -y
pip install PyGithub
pip install boto3
git clone https://gitlab.com/Rusllan/odoo-devops.git /home/ec2-user/odoo-devops
sudo chmod +x /home/ec2-user/odoo-devops/tools/merge-bot/ec2/ec2-run.py
sudo chmod +x /home/ec2-user/odoo-devops/tools/merge-bot/scripts/merge.py
sudo chmod +x /home/ec2-user/odoo-devops/tools/merge-bot/scripts/fork.py
sudo chmod +x /home/ec2-user/odoo-devops/tools/merge-bot/scripts/clone_fork.py
sudo chmod +x /home/ec2-user/odoo-devops/tools/merge-bot/scripts/pull-request.py
sudo echo "*/5 * * * * sudo /usr/bin/python /home/ec2-user/odoo-devops/tools/porting-bot/ec2/ec2-run.py" >> mycron
sudo echo "@reboot sudo /usr/bin/python /home/ec2-user/odoo-devops/tools/porting-bot/ec2/ec2-run.py" >> mycron
sudo crontab mycron
sudo python /home/ec2-user/odoo-devops/tools/merge-bot/ec2/ec2-run.py
