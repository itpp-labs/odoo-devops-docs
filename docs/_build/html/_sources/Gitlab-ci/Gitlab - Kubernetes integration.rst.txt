Gitlab - Kubernetes integration
=======================================

You can easily connect existing Kubernetes cluster to your GitLab project. With connected cluster you can use Review Apps, deploy your applications and run your pipelines.

Adding an existing Kubernetes cluster
-------------------------------------

In order to add your existing Kubernetes cluster to your project:

* Navigate to your project's Operations > Kubernetes page.

* Click on Add Kubernetes cluster.

* Click on Add an existing Kubernetes cluster and fill in the details:

	* Kubernetes cluster name (required) - The name you wish to give the cluster.
        * Environment scope (required) - The associated environment to this cluster. You can leave it with "*".
	* API URL (required) - It's the URL that GitLab uses to access the Kubernetes base API. You can access it locally with cubectl proxy and need to make it accessible externially. In the end you should have something like "https://kubernetes.example.com".
	* CA certificate (optional) - If the API is using a self-signed TLS certificate, you'll also need to include the ca.crt contents here.
	* Token - GitLab authenticates against Kubernetes using service tokens, which are scoped to a particular namespace. If you don't have a service token yet, you can follow the Kubernetes documentation to create one. You can also view or create service tokens in the Kubernetes dashboard (under Config > Secrets). The account that will issue the service token must have admin privileges on the cluster.
	* Project namespace (optional) - You don't have to fill it in; by leaving it blank, GitLab will create one for you. 

* Click on Create Kubernetes cluster.

After a couple of minutes, your cluster will be ready to go.

If you using Minukube cluster or just have Kubernetes Dashboard you can get CA certificate and token in Dashboard. You need to choose default namespace and click on secrets. There should be default token with CA and token inside.

Installing applications
-----------------------

GitLab provides a one-click install for some applications which will be added directly to your connected Kubernetes cluster.

To one-click install applications:

* Navigate to your project's Operations > Kubernetes page.

* Click on your connected cluster.

* Click install button beside the application you need.

You need to install Helm Tiller before you install any other application
