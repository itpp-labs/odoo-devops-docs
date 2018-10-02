Minikube
=======================================

Minikube is easiest way to run single-node Kubernetes cluster locally. Setup is completely automated so it is just matter of installation and starting the cluster. 

Installing Minikube
-------------------

In order to install Minikube you need to:

* Enable Intel Virtualization Technology or AMD virtualization in your computer’s BIOS
* Install `VirtualBox <https://www.virtualbox.org/wiki/Downloads>`_ or alternatively you can install other hypervisors: VMware Fusion, HyperKit, KVM or Hyper-V depending on your OS
* Install `kubectl <https://kubernetes.io/docs/tasks/tools/install-kubectl/>`_ according to the instructions
* Install latest `Minikube <https://github.com/kubernetes/minikube/releases>`_

Starting Minukube
-----------------
To start cluster you can just run:
::

	minikube start

Depending on the hypervisor you want to use you can specifiy it by --vm-driver option and choose amount of memory you want Minikube to use:
::

	minikube start --memory 4096 --vm-driver virtualbox

Minikube also supports a --vm-driver=none option that runs the Kubernetes components on the host and not in a VM. In this case you should have Docker installed.

Iteract with your cluster
-------------------------

Now you can access your cluster with kubectl proxy:

::

	kubectl proxy --port=8001 &

And you can get the API with curl or any browser:

::

	curl http://localhost:8001/api/

Dashboard
---------

Minikube automaticly have Kubernetes Dashboard - web-based UI for Kubernetes clusters. It allows you to monitor and manage aplications on your cluster.

To access dashboard you can just type in console:
::
	minikube dashboard

And it will open in your default browser. 

Or to get url you can run:
::
	minikube dashboard --url

Stopping Minikube
-----------------

To stop your cluster just run:

::
	
	minikube stop



