# Github bot Scripts

This is scripts which Github bot uses, but they can be used separately to do the same thing manually.

To use any script you will need to:

* Download scripts:

      $ git clone git@gitlab.com:itpp/odoo-devops.git 

* Give script you need required permissions: 

      sudo chmod +x odoo-devops/tools/merge-bot/<script name>.py
      
* Create a symbolic link to script:

      sudo ln -s $(pwd)/odoo-devops/tools/merge-bot/<script name>.py /usr/local/bin

### merge.py

Script for automatically merging branches with modules, which have different odoo versions. This allow to transfer module changes between versions easier.

Currently it creates a new branch that is ready to merge in branch you choosed and solve some version conflicts in manifest.py files

In order to merge branches you will need: cloned repository with odoo modules and set up remotes "origin" and "upstream", or you can use alternative names for them via script arguments.

* Upstream remote will be used to fork branches for merge.
* Origin remote will be used to send pull request to

To use merge script:

* Run merge.py with 2 arguments:

      $ merge.py <from_branch> <in_branch>

* Push branch in your repository:

      $ git push origin
      
Where positional arguments are:
* from_branch - Name of branch, from which merge will be made.
* in_branch - Name of branch, in which merge will be made.

And optional ones for setting up alternative names for remotes:
* --upstream_remote - will be used as name for "upstream" remote. Default value is "upstream".
* --origin_remote - will be used as name for "origin" remote. Default value is "origin".
* --new_branch_name - name for branch which will be created.
* --auto_resolve - option for making some automatic resolving.
* --auto_push - option for automatically push branch to origin repository.

Merge example of pos-addons from 11.0 to 12.0:

* Checking if needed remotes are in place:

      $ git remote -v

      origin	git@github.com:Rusllan/pos-addons.git (fetch)
      origin	git@github.com:Rusllan/pos-addons.git (push)
      upstream	git@github.com:it-projects-llc/pos-addons.git (fetch)
      upstream	git@github.com:it-projects-llc/pos-addons.git (push)

* Running the script: 

      $ merge-bot.py 11.0 12.0
      
* Push changes to origin repo:

      $ git push origin
      
Result of this merge you can see in PR: https://github.com/it-projects-llc/misc-addons/pull/682

### review.py

Script for making review to specified pull request. Review contains list of updated modules and list of changes that need to be tested.

To use review script:

* Run review.py with 2 arguments:

      $ review.py <repo_name> <pr_number>

Where positional arguments are:
* repo_name - Name of repository where review will be made.
* pr_number - Number of PR in which review will be made.

And optional ones for setting up alternative names for remotes:
* --github_login - Login from github account.
* --github_password - Password from github account.
* --github_token - Token from github account. Token or login/passord not specified will be taken from GITHUB_TOKEN_FOR_BOT environmental variable.

### pull-request.py

Script for making pull request with specified branch to specified repository. Review contains list of updated modules and list of changes that need to be tested.

To use pull-request script:

* Run pull-request.py with 4 arguments:

      $ pull-request.py <base_repo_name> <base_branch> <forked_user> <head_branch>

Where positional arguments are:
* base_repo_name - Name of repository where PR will be made.
* base_branch - Name of branch, in which merge will be made.
* forked_user - Name of the user who own a fork where branch is located.
* head_branch - Name of branch, from where merge will be made.

And optional ones for setting up alternative names for remotes:
* --github_login - Login from github account.
* --github_password - Password from github account.
* --github_token - Token from github account. Token or login/passord not specified will be taken from GITHUB_TOKEN_FOR_BOT environmental variable.
