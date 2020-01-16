.. code-block:: sh

    sshfs -p 22 -o idmap=user,nonempty USERNAME@REMOTE-SERVER:/path/to/REMOTE/folder /path/to/LOCAL/folder