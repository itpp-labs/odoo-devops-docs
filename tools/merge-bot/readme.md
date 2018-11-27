Merge bot for transfering changes between odoo versions 
=======================================================

This is scripts for automaticly merging branches with modules, which have different odoo versions. This allow to transfer module changes between versions more easier and with the lowest possible human participation.

Currently they creating a new branch that is ready to merge in branch you choosed

To use scripts you need to:

* Download scripts:
	
	git clone git@gitlab.com:itpp/odoo-devops.git 

* Go inside merge-bot folder.

* Run merge-bot.py with 5 arguments:

	merge-bot.py <repo_name> <from_account> <fork_account> <from_branch> <in_branch>

Where arguments are:

* repo_name - Name of repository where merge will be made
* from_account - Account where repository, in witch PR will be made, is located
* fork_account - Account where repository, in which branch will be created, is located
* from_branch - Name of branch, from which merge will be made
* in_branch - Name of branch, in which merge will be made
