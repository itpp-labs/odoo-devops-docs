==================================
 Creating Pull Requests in batch
==================================

Prerequisites
=============

* Add a SSH key to your GitHub account. See: https://help.github.com/en/articles/adding-a-new-ssh-key-to-your-github-account
* Install hub. Look this: https://github.com/github/hub#installation 

Script
======

Make a script ``make-prs.sh`` with following content

.. code-block:: bash

    #!/bin/bash

    # ORGANIZATION GITHUB URL
    ORG=it-projects-llc
    UPSTREAM_URL_GIT=https://github.com/$ORG

    # DEVELOPER INFO
    USERNAME=yelizariev

    # WHERE TO CLONE
    DIRECTORY_CLONE=./

    # DESCRIPTION OF THE UPDATES
    MSG=":shield: travis.yml notifications webhook travis"
    BRANCH_SUFFIX=travis-notifications

    REPOS=(
        misc-addons
        saas-addons
        pos-addons
        access-addons
        mail-addons
        website-addons
        sync-addons
	)
    BRANCHES=(
        10.0
        11.0
        12.0
	)

    for REPO in "${REPOS[@]}"; do
        if [ ! -d $DIRECTORY_CLONE/$REPO ]
        then
            git clone $UPSTREAM_URL_GIT/$REPO.git $DIRECTORY_CLONE/$REPO
            cd $DIRECTORY_CLONE/$REPO
            git remote rename origin upstream
            git remote add origin git@github.com:$USERNAME/$REPO.git
        fi
        cd $DIRECTORY_CLONE/$REPO
        for BRANCH in "${BRANCHES[@]}"; do
            git checkout -b $BRANCH-$BRANCH_SUFFIX upstream/$BRANCH

            # CHECK THAT UPDATES ARE NOT DONE YET
            if grep -qx '    on_failure: change' .travis.yml
            then
                echo "File are already updated in $REPO#$BRANCH"
            else
                # MAKE UPDATE
                { echo '  webhooks:'; echo '    on_failure: change'; echo '  urls:'; echo '    - "https://ci.it-projects.info/travis/on_failure/change"';} >> ./.travis.yml
            fi
            git commit -a -m "$MSG"
            git push origin $BRANCH-$BRANCH_SUFFIX
            hub pull-request -b it-projects-llc:$BRANCH -m "$MSG"
        done
    done

Update script according to you needs

Run it with ``bash make-prs.sh``

