======================================
 How to mount local files on a server
======================================


sshfs
=====

On your local machine:

.. code-block:: sh

    # Step 1. Install ssh server on your local machine
    # TODO
    # Step 2. Configure ssh keys on you local machine
    cat cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys 
    # Step 3. Connect to your server
    ssh USERNAME@SERVER -p 22 -A -R 2222:localhost:22


On your remote server:

.. code-block:: sh

    # Step 4. Mount your directory on remote server
    # about allow_other check this: https://github.com/moby/moby/issues/27026#issuecomment-253579983 
    sshfs -p 2222 -o idmap=user,nonempty,allow_other \
                 LOCALUSERNAME@127.0.0.1:/PATH/TO/LOCAL/FOLDER /PATH/TO/REMOTE/FOLDER

    # to unmount:
    fusermount -u /PATH/TO/REMOTE/FOLDER

References
==========

* https://superuser.com/questions/616182/how-to-mount-local-directory-to-remote-like-sshfs
