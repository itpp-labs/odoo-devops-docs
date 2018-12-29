Merge bot for transfering changes between odoo versions 
=======================================================

This is scripts for automatically merging branches with modules, which have different odoo versions. This allow to transfer module changes between versions more easier and with the lowest possible human participation.

Currently they creating a new branch that is ready to merge in branch you choosed and solve some version conflicts in manifest.py files

In order to merge branches you will need: cloned repository with odoo modules and set up remotes "origin" and "upstream", or you can use alternative names for them via script arguments.

* Upstream remote will be used to fork branches for merge.
* Origin remote will be used to send pull request to

To use scripts you need to:

* Download scripts:

      $ git clone git@gitlab.com:itpp/odoo-devops.git 

* Give script required permissions: 

      sudo chmod +x odoo-devops/tools/merge-bot/merge-bot.py
      
* Create a symbolic link to script:

      sudo ln -s $(pwd)/odoo-devops/tools/merge-bot/merge-bot.py /usr/local/bin

* Run merge-bot.py with 2 arguments:

      $ merge-bot.py <from_branch> <in_branch>

* Push branch in your repository:

      $ git push origin
      
Where positional arguments are:
* from_branch - Name of branch, from which merge will be made
* in_branch - Name of branch, in which merge will be made

And two optional ones for setting up alternative names for remotes:
--upstream_remote - will be used as name for "upstream" remote. Default value is "upstream".
--origin_remote - will be used as name for "origin" remote. Default value is "origin".
--auto_resolve - option for making some automatic resolving.
--auto_push - option for automatically push branch to origin repository.

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
