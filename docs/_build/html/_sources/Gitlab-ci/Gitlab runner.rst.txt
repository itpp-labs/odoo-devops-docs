GitLab Runner
=======================================

There is a different ways to install GitLab Runner on your Kubernetes cluster.

One-click install
-----------------

If your Kubernetes cluster is connected to your GitLab project you can just:

* Navigate to your project's Operations > Kubernetes page.

* Click on your connected cluster.

* Install Helm Tiller by clicking the install button beside it.

* Install GitLab Runner by clicking the install button beside it.

Deploy GitLab Runner manually
-----------------------------

If you want to cofigure everything yourself, you can deploy runner manually.

First you need to create namespace for your future deployment:
::

	kubectl create namespace gitlab-runner-ns

To check your current namespaces:
::

	kubectl get namespaces

Now set created namespace as default:
::

	kubectl config set-context $(kubectl config current-context) --namespace=gitlab-runner-ns

To deployment we will need to create a deployment.yaml, config-map.yaml and secret.yaml.

Start with config-map.yaml:
::

	apiVersion: v1
	kind: ConfigMap
	metadata:
	  name: gitlab-runner-cm
	  namespace: gitlab-runner-ns
	data:
	  config.toml: |
	    concurrent = 10
	    check_interval = 30

	  entrypoint: |
	    #!/bin/bash

	    set -xe

	    cp /scripts/config.toml /etc/gitlab-runner/

	    # Register the runner
	    /entrypoint register --non-interactive \
	      --url $GITLAB_URL \
	      --executor kubernetes

	    # Start the runner
	    /entrypoint run --user=gitlab-runner \
	      --working-directory=/home/gitlab-runner

And create config map with:
::

	kubectl create -f config-map.yaml 

For sake of not showing your token in clear in your deployment file we need to create secret.yaml with token as base 64 string:
::

	echo -n "your_token" | base64
	
::

	apiVersion: v1
	kind: Secret
	metadata:
	  name: gitlab-runner-secret
	  namespace: gitlab-runner-ns
	type: Opaque
	data:
	  runner-registration-token: <your token as base 64 string>

Now, create secret with:
::

	kubectl create --validate -f secret.yaml

And finally deployment.yaml file:
::

	apiVersion: extensions/v1beta1
	kind: Deployment
	metadata:
	  name: gitlab-runner
	  namespace: gitlab-runner-ns
	spec:
	  replicas: 1
	  selector:
	    matchLabels:
	      name: gitlab-runner
	  template:
	    metadata:
	      labels:
		name: gitlab-runner
	    spec:
	      containers:
		- name: gitlab-runner
		  image: gitlab/gitlab-runner:alpine-v9.3.0
		  command: ["/bin/bash", "/scripts/entrypoint"]
		  env:
		    - name: GITLAB_URL
		      value: "https://gitlab.com/"
		    - name: REGISTRATION_TOKEN
		      valueFrom:
		        secretKeyRef:
		          name: gitlab-runner-secret
		          key: runner-registration-token
		  imagePullPolicy: Always
		  volumeMounts:
		    - name: config
		      mountPath: /scripts
		    - name: cacerts
		      mountPath: /etc/gitlab-runner/certs
		      readOnly: true
	      restartPolicy: Always
	      volumes:
		- name: config
		  configMap:
		    name: gitlab-runner-cm
		- name: cacerts
		  hostPath:
		    path: /var/mozilla

For creating runners gitlab needs ClusterRoleBinding with cluster-admin role. So before deploying we creating cluster role:
::

	kubectl create clusterrolebinding gitlab-cluster-admin --clusterrole=cluster-admin --group=system:serviceaccounts --namespace=gitlab-runner-ns

And now creating deployment:
::

	kubectl create --validate -f deployment.yaml
