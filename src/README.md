# Charm Magnum


Charm to deploy Magnum in a Canonical OpenStack deployment


## Build charm

```bash
export CHARM_BASE="$HOME/work/charms"
export JUJU_REPOSITORY="$CHARM_BASE/build"
export CHARM_INTERFACES_DIR="$CHARM_BASE/interfaces"
export CHARM_LAYERS_DIR="$CHARM_BASE/layers"

mkdir -p $JUJU_REPOSITORY
mkdir $CHARM_INTERFACES_DIR
mkdir $CHARM_LAYERS_DIR

git clone https://github.com/oprinmarius/magnum-charm
sudo snap install --classic charm

cd magnum-charm
charm build
```

You should now have a charm built in ```$JUJU_REPOSITORY/builds/charm-magnum```.

## Deploy charm

```bash
juju deploy $JUJU_REPOSITORY/builds/charm-magnum magnum --config openstack-origin="cloud:bionic-train"

juju add-relation magnum mysql
juju add-relation magnum rabbitmq-server
juju add-relation magnum:identity-service keystone:identity-service
```

After the charm is deployed and all relations have been established, you must run the ```domain-setup``` action to finalize the deployment. This action can be run on any unit.

```bash
juju run-action magnum/0 domain-setup
```
