from __future__ import absolute_import

import binascii
import os

import charm.openstack.magnum.magnum as magnum  # noqa
import charms.reactive as reactive
import charms.leadership as leadership
import charms_openstack.charm as charm
import charmhelpers.core.hookenv as hookenv

from charmhelpers.contrib.openstack import context
from charmhelpers.core import templating

# Use the charms.openstack defaults for common states and hooks
charm.use_defaults(
    'charm.installed',
    'amqp.connected',
    'shared-db.connected',
    'identity-service.available',  # enables SSL support
    'config.changed',
    'update-status',
    'upgrade-charm',
    'certificates.available',
    'cluster.available')


@reactive.when('shared-db.available')
@reactive.when('identity-service.available')
@reactive.when('amqp.available')
def render_config(*interfaces):
    with charm.provide_charm_instance() as magnum_charm:
        magnum_charm.render_with_interfaces(interfaces)
        magnum_charm.assess_status()
    reactive.set_state('config.complete')


@reactive.when('certificates.available')
@reactive.when('shared-db.available')
@reactive.when('identity-service.available')
@reactive.when('amqp.available')
def render_config_with_certs(amqp, keystone, shared_db, certs):
    with charm.provide_charm_instance() as magnum_charm:
        magnum_charm.configure_tls(certs)
        magnum_charm.render_with_interfaces(
            [amqp, keystone, shared_db, certs])


@reactive.when('identity-service.connected')
def setup_endpoint(keystone):
    magnum.setup_endpoint(keystone)
    magnum.assess_status()


@reactive.when_not('leadership.set.magnum_password')
@reactive.when('leadership.is_leader')
def generate_magnum_password():
    passwd = binascii.b2a_hex(os.urandom(32)).decode()
    leadership.leader_set({'magnum_password': passwd})


@reactive.when('leadership.set.magnum_password')
@reactive.when('leadership.is_leader')
@reactive.when('identity-service.available')
def write_openrc():
    config = hookenv.config()
    ctx = context.IdentityServiceContext()()
    if not ctx:
        return
    ctx["region"] = config.get("region")
    templating.render("openrc_v3", "/root/openrc_v3", ctx)


@reactive.when('config.complete')
@reactive.when_not('db.synced')
def run_db_migration():
    with charm.provide_charm_instance() as magnum_charm:
        magnum_charm.db_sync()
        magnum_charm.restart_all()
        magnum_charm.assess_status()
    reactive.set_state('db.synced')


@reactive.when('ha.connected')
@reactive.when_not('ha.available')
def connect_cluster(hacluster):
    with charm.provide_charm_instance() as magnum_charm:
        magnum_charm.configure_ha_resources(hacluster)
        magnum_charm.assess_status()
