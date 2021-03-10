# Overview

This charm provides the Magnum service for an OpenStack Cloud.

OpenStack Ussuri or later is required.

# Usage

Magnum and the Magnum charm relies on services from a fully functional
OpenStack Cloud and expects to be able to consume images from glance, consume certificate secrets from Barbican (preferably
utilizing a Vault backend) and spin up Kubernetes clusters with Heat.
Magnum requires the existence of the other core OpenStack services deployed via Juju charms, specifically: mysql, rabbitmq-server, keystone and nova-cloud-controller. The following assumes these services have already been deployed.

## Required configuration

After deployment of the cloud, the domain-setup action must be run to configure required domains, roles and users in the cloud
for Magnum clusters.

```bash
juju run-action magnum/0 domain-setup
```

Magnum generates and maintains a certificate for each cluster so that it can also communicate securely with the cluster. As a result, it is necessary to store the certificates in a secure manner. Magnum provides the following methods for storing the certificates and this is configured in /etc/magnum/magnum.conf in the section [certificates] with the parameter
`cert_manager_type`
  Valid values are : [barbican, x509keypair, local]

`trustee-domain`
    - Domain used for COE

`trustee-admin`
    - Domain admin for the trustee-domain

## Deploy a Kubernetes cluster

When Magnum deploys a Kubernetes cluster, it uses parameters defined in the ClusterTemplate and specified on the
cluster-create command, for example:

```bash
openstack coe cluster template create k8s-cluster-template \
                           --image fedora-coreos-latest \
                           --keypair testkey \
                           --external-network public \
                           --dns-nameserver 8.8.8.8 \
                           --flavor m1.small \
                           --docker-volume-size 5 \
                           --network-driver flannel \
                           --coe kubernetes
```
```bash
openstack coe cluster create k8s-cluster \
                      --cluster-template k8s-cluster-template \
                      --master-count 3 \
                      --node-count 8
```

Refer to the [ClusterTemplate][cltempl] and [Cluster][cl] sections for the full list of parameters.

This section covers common and/or important configuration options. See file config.yaml for the full list of options, along with their descriptions and default values. See the Juju documentation for details on configuring applications.

# High availability

When more than one unit is deployed with the hacluster application the charm will bring up an HA active/active cluster.

There are two mutually exclusive high availability options: using virtual IP(s) or DNS. In both cases the hacluster subordinate charm is used to provide the Corosync and Pacemaker backend HA functionality.

See Infrastructure high availability in the OpenStack Charms Deployment Guide for details.

# Bugs

Please report bugs on [Launchpad][lp-bugs-charm-magnum].

For general charm questions refer to the OpenStack [Charm Guide][cg].

<!-- LINKS -->

[cg]: https://docs.openstack.org/charm-guide
[lp-bugs-charm-magnum]: https://bugs.launchpad.net/charm-magnum/+filebug
[cltempl]: https://docs.openstack.org/magnum/latest/user/#clustertemplate
[cl]: https://docs.openstack.org/magnum/latest/user/#cluster