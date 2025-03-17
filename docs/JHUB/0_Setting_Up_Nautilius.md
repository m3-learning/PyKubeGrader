# Running on Nautilus

Nautilus is a NSF supported Kubernetes cluster which is federated across many institutions. It is a great place to run jobs on high-availability clusters. There are, however, some limitations regarding the load balancer.

:exclamation: If you are going to run for a semester, you will need to contact the Nautilus team to ensure persistance.

## Creating and Accessing a Nautilus Account

Go to this website to create an account: [Nautilus](https://portal.nrp-nautilus.io/)

## Quick Start Guide

### Please note:

:exclamation: Containers are stateless. ALL your data WILL BE GONE FOREVER when container restarts, unless you store in a persistent volume.

:exclamation: Container restart is normal in k8s cluster. Expect it.

:exclamation: NEVER FORCE DELETE PODS

:exclamation: Users running a Job with "sleep" command or equivalent (any command that never ends by itself) will be banned from using the cluster.

1. [Install][1] the kubectl tool
2. Login to [NRP Nautilus portal][2] and click the **Get Config** link on top right corner of the page to get your configuration file.

   :exclamation: Make sure you use the same provider and account you used to login to the portal. If you use the different provider with the same email, your account in the system will still be different and your namespaces membership will change.

3. Save the file as **config** and put the file in your <home>/.kube folder.

   This folder may not exists on your machine, to create it execute:

   ```
   mkdir ~/.kube
   ```

4. Any cluster admin can promote you to admin (ask in [Matrix](/userdocs/start/contact/), provide your affiliation and short project description), or any admin can promote you to user by adding to one of namespaces (contact the admin directly). Make sure you are promoted from **guest** to **user** (by joining an existing namespace) or to **admin** by getting a confirmation from either admin or cluster admin.

5. **If you've become an admin**, you can start creating your own namespaces at this time by going to the [**Namespaces**](https://portal.nrp-nautilus.io/profileN) section in the portal. Also you can add other users on the same page after they've logged in to the portal. If you're joining an existing namespace as a user, make sure your namespace's admin added you to it. To verify it go to **Namespaces** link (while logged on the portal).

6. Test kubectl can connect to the cluster using a command line tool:

   ```
   kubectl get pods -n your_namespace
   ```

   It's possible there are no pods in your namespace yet. If you've got `No resources found.`, this indicates your namespace is empty and you can start running in it.

7. To learn more about kubernetes you can look at [our tutorial](/userdocs/tutorial/basic/).

   These resources might be helpful:

   - [kubectl tool overview][4] and [cheatsheet][6]
   - [kubernetes basics][3] from kubernetes project
   - [tutorials][5]

   Please note that not all examples will work in our cluster because of security policies. You are limited to see what's happening in your own namespace, and nobody else can see your running pods.

8. **MANDATORY**: read the [Policies](/userdocs/start/policies/) page

9. [Proceed](/userdocs/running/jobs/) to creating your first ML job in kubernetes

10. You might want to try one of these GUI tools for Kubernetes:

    - [Lens](https://k8slens.dev/) - Graphical user interface
    - [K9s](https://k9scli.io/) - console graphical user interface

Both will use your config file in default location to get access to the cluster.

[1]: https://kubernetes.io/docs/tasks/tools/install-kubectl/
[2]: https://portal.nrp-nautilus.io/
[3]: https://kubernetes.io/docs/tutorials/
[4]: https://kubernetes.io/docs/reference/kubectl/overview/
[5]: https://kubernetes.io/docs/tutorials/
[6]: https://kubernetes.io/docs/reference/kubectl/cheatsheet/
