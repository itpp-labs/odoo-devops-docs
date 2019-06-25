==================================
 GitHub script for pull requests
==================================


Use it script for make pull requests for all repos all branches
---------------------------------------------------------------

* Add a new SSH key to your GitHub account. See: https://help.github.com/en/articles/adding-a-new-ssh-key-to-your-github-account
* Create new <your file> in your work directory, copy-paste and update this code:

.. code-block:: console

    #!/bin/bash

    UPSTREAM_URL_GIT=https://github.com/it-projects-llc
    ORIGIN_URL_GIT=https://github.com/kaadevelop
    DIRECTORY_CLONE=$HOME/odoo/bash/repos
    USERNAME=kaadevelop
    MSG=":shield: travis.yml notifications webhook travis"
    REPOS=(
        misc-addons
        #saas-addons
        pos-addons
        access-addons
        mail-addons
        website-addons
	)
    BRANCHES=(
        10.0
        11.0
        12.0
	)

    for REPO in "${REPOS[@]}"; do
        git clone $UPSTREAM_URL_GIT/$REPO.git $DIRECTORY_CLONE/$REPO
        cd $DIRECTORY_CLONE/$REPO
        git remote rename origin upstream
        git remote add origin $ORIGIN_URL_GIT/$REPO.git
        git remote set-url origin git@github.com:$USERNAME/$REPO.git
        for BRANCH in "${BRANCHES[@]}"; do
            git branch $BRANCH upstream/$BRANCH
            git checkout $BRANCH
            if grep -qx '    on_failure: change' .travis.yml
            then
                echo "Hola!"
            else
                { echo '  webhooks:'; echo '    on_failure: change'; echo '  urls:'; echo '    - "https://ci.it-projects.info/travis/on_failure/change"';} >> ./.travis.yml
                git add .travis.yml
                git commit -m "$MSG"
                git push origin -f $BRANCH
                hub pull-request -b it-projects-llc:$BRANCH -m "$MSG"
            fi
        done
    done

* Install hub. Look this: https://github.com/github/hub#installation 
* Run your file in terminal from your work directory:

  * ``sudo chmod +x <your file>``
  * ``./<your file>``

