=============
 Lint Checks
=============

Preparation
===========

Execute once per computer

.. code-block:: sh

    cd
    git clone https://github.com/it-projects-llc/maintainer-quality-tools.git
    cd maintainer-quality-tools/travis
    LINT_CHECK="1" sudo -E bash -x travis_install_nightly 8.0

    echo "export PATH=\$PATH:$(pwd)/" >> ~/.bashrc
    source ~/.bashrc

Running checks
==============


.. code-block:: sh

    cd YOUR-PATH/TO/REPOSTORY
    LINT_CHECK="1" TRAVIS_BUILD_DIR="." VERSION="12.0" travis_run_tests 12.0
