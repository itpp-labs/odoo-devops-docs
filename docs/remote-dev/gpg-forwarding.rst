WIP

======================
 GPG Agent Forwarding
======================

To sign your commit on remote server you can forward gpg agent via ssh.

* Execute on local and remote matchine::

       gpgconf --list-dir agent-extra-socket

  It will give something like ``/run/user/1000/gnupg/S.gpg-agent.extra``.

* Now you need to modify ``/etc/ssh/sshd_config`` on remote server and set following setting::

       StreamLocalBindUnlink yes

  Save the file and restart ssh server, e.g.::
  
       sudo service ssh restart

* Then on connecting to the server add following arg::

       ssh user@domain.example -R /run/user/1000/gnupg/S.gpg-agent.extra:/run/user/1000/gnupg/S.gpg-agent.extra

  You can also configure it in ``~/.ssh/config`` file::

       Host gpgtunnel
       HostName domain.example
       RemoteForward <socket_on_remote_box>  <extra_socket_on_local_box>
 
 
References: 
* https://wiki.gnupg.org/AgentForwarding
* https://superuser.com/questions/161973/how-can-i-forward-a-gpg-key-via-ssh-agent
