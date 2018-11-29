Merge bot for transfering changes between odoo versions 
=======================================================

This is scripts for automaticly merging branches with modules, which have different odoo versions. This allow to transfer module changes between versions more easier and with the lowest possible human participation.

Currently they creating a new branch that is ready to merge in branch you choosed. 

In order to merge branches you will need: cloned repository with odoo modules and set up remotes "origin" and "upstream", or you can use alternative names for them via script arguments.

* Upstream remote will be used to fork branches for merge.
* Origin remote will be used to send pull request to

To use scripts you need to:

* Download scripts:

      git clone git@gitlab.com:itpp/odoo-devops.git 

* Copy file merge-bot.py from tools/merge-bot folder in your repository folder with odoo modules

* Run merge-bot.py with 2 arguments:

      python merge-bot.py <from_branch> <in_branch>

Where positional arguments are:
* from_branch - Name of branch, from which merge will be made
* in_branch - Name of branch, in which merge will be made

And two optional ones for setting up alternative names for remotes:
--upstream_remote - will be used as name for "upstream" remote. Default value is "upstream".
--origin_remote ORIGIN_REMOTE - will be used as name for "origin" remote. Default value is "origin".