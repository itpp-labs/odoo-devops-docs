# Github bot

This is bot for transferring changes between different Odoo versions and writing review. It based on Amazon Web Services (EC2, Lambda, SQS) and python scripts.

## Deploy

In order to deploy bot and set it up for your repository you will need to:

* Have repository with your odoo modules. Like [this one](github.com/it-projects-llc/pos-addons);

* Register or login on Amazon Web Services site [here](aws.amazon.com);

* Go to your [AWS Management Console](console.aws.amazon.com);

* In AWS Management Console click on your login in top right corner and then click on "My Security Credentials";

* In My Security Credentials page click on "Access keys (access key ID and secret access key)";

* Now click on "Create New Access Key" and download the key;

* Follow up [this](docs.aws.amazon.com/en_us/cli/latest/userguide/cli-chap-install.html) instruction for installing AWS CLI;

* Follow up [this](docs.aws.amazon.com/en_us/cli/latest/userguide/cli-chap-configure.html) instruction to configure AWS CLI. Use Access Key and Secret Access Key witch you downloaded from AWS Management Console;

* Clone repository odoo-devops repository:
    
      $ git clone git@gitlab.com:itpp/odoo-devops.git 

* Install Boto3 package with pip or pip3:

      $ pip install boto3
      
*