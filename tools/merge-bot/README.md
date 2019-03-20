# Github bot

This is bot for transferring changes between different Odoo versions and writing review. It based on Amazon Web Services (EC2, Lambda, SQS) and python scripts.

## Requirements 

For bot deployment you will need:

* Github repository with your odoo modules. Like [this one](github.com/it-projects-llc/pos-addons);

* Account in Github from witch pull requests and reviews will be made.

* Account in [Amazon Web Services](aws.amazon.com);

## Deployment and setup

In order to deploy bot and set it up for your repository you will need to:

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
      
* Login in your Github account (from witch pull requests and reviews will be made) and go to [personal access tokens page](github.com/settings/tokens);

* Click on "Generate new token" button and select "repo" in scopes. Then click on "Generate token" and save yout generated token;

* Set local environment variable GITHUB_TOKEN_FOR_BOT with value of your Github token:

      $ export GITHUB_TOKEN_FOR_BOT=<your Github token>
      
* Run ec2-deploy.py script (you can use python3 instead):

      $ python ./odoo-devops/tools/merge-bot/ec2/ec2-deploy.py
      
-------
This part of instruction will be deleted when it will be automated and made part of ec2-deploy.py.

* Go to [AWS Lambda page](console.aws.amazon.com/lambda/home) and click on github-bot-lambda;

* Now click on "API Gateway" button on the left panel to crate API Gateway for your Lambda function;

* In the panel that appears below pick "Create a new API" and "Open" (you also can choose other security mechanism but it will require additional set up) and click "Add";

* Click on "Save" button on the top right corner and copy your API endpoint in below panel;
-------

* Login in your Github account (one with repository for witch you want use bot) and go to the repository page;

* Click on "Settings" and then on "Webhooks" button;

* Click on "Add webhook" and enter your API endpoint to Payload URL field. Choose "application/json" in "Content type" field;

* In field "Which events would you like to trigger this webhook?" press "Let me select individual events.", then choose "Pull requests" and press on "Add webhook".

## Usage

When bot is deployed and set up to one or more repositories it will make reviews with changes for testing and list with all changed modules in all new pull requests.

Transfer of changes between branches will soon be implemented and documented.

More information can be obtained in scripts/README.md file, where scripts witch bot uses described.