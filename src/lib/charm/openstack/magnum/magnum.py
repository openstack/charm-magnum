from __future__ import absolute_import

import collections
import os

import charms.leadership as leadership
import charms_openstack.charm
import charms_openstack.adapters as adapters
import charms_openstack.ip as os_ip
import charmhelpers.core.host as ch_host
import charmhelpers.core.hookenv as ch_hookenv
import charmhelpers.fetch as fetch


PACKAGES = [
    'magnum-api',
    'magnum-conductor',
    'python3-mysqldb',
    'python3-magnumclient']

MAGNUM_DIR = '/etc/magnum/'
MAGNUM_CONF = os.path.join(MAGNUM_DIR, 'magnum.conf')
MAGNUM_PASTE_API = os.path.join(MAGNUM_DIR, 'api-paste.ini')
KEYSTONE_POLICY = os.path.join(MAGNUM_DIR, 'keystone_auth_default_policy.json')
POLICY = os.path.join(MAGNUM_DIR, 'policy.json')

MAGNUM_SERVICES = [
    'magnum-api',
    'magnum-conductor']


# select the default release function
charms_openstack.charm.use_defaults('charm.default-select-release')


@adapters.config_property
def magnum_password(arg):
    passwd = leadership.leader_get("magnum_password")
    if passwd:
        return passwd


@adapters.config_property
def ca_file_path(arg):
    file_path = os.path.join(
        ch_host.CA_CERT_DIR, "{}.crt".format(ch_hookenv.service_name()))
    if os.path.exists(file_path):
        return file_path
    return ''


def db_sync_done():
    return MagnumCharm.singleton.db_sync_done()


def restart_all():
    MagnumCharm.singleton.restart_all()


def db_sync():
    MagnumCharm.singleton.db_sync()


def configure_ha_resources(hacluster):
    MagnumCharm.singleton.configure_ha_resources(hacluster)


def assess_status():
    MagnumCharm.singleton.assess_status()


def setup_endpoint(keystone):
    charm = MagnumCharm.singleton
    public_ep = '{}/v1'.format(charm.public_url)
    internal_ep = '{}/v1'.format(charm.internal_url)
    admin_ep = '{}/v1'.format(charm.admin_url)
    keystone.register_endpoints(charm.service_type,
                                charm.region,
                                public_ep,
                                internal_ep,
                                admin_ep)


class MagnumCharm(charms_openstack.charm.HAOpenStackCharm):

    abstract_class = False
    release = 'ussuri'
    name = 'magnum'
    packages = PACKAGES
    python_version = 3
    api_ports = {
        'magnum-api': {
            os_ip.PUBLIC: 9511,
            os_ip.ADMIN: 9511,
            os_ip.INTERNAL: 9511,
        }
    }
    service_type = 'magnum'
    default_service = 'magnum-api'
    services = MAGNUM_SERVICES
    sync_cmd = ['magnum-db-manage', 'upgrade']

    required_relations = [
        'shared-db', 'amqp', 'identity-service']

    restart_map = {
        MAGNUM_CONF: services,
        MAGNUM_PASTE_API: [default_service, ],
        KEYSTONE_POLICY: services,
        POLICY: services,
    }

    ha_resources = ['vips', 'haproxy']

    # Package for release version detection
    release_pkg = 'magnum-common'

    # Package codename map for magnum-common
    package_codenames = {
        'magnum-common': collections.OrderedDict([
            ('10', 'ussuri'),
            ('11', 'victoria'),
        ]),
    }

    group = "magnum"

    # TODO: Remove this 'install' hook wrapper once the Magnum packages are
    # fixed in the cloud archive / default repositories.
    # We use a 3rd party PPA with custom Magnum packages (built against
    # Magnum stable branch) because they include a couple of needed fixes.
    # Due to the amount of changes needed to fix Magnum Ussuri, we went with
    # the separate PPA to have the charm working.
    # A good indication that Magnum is fixed in the cloud archive / default
    # repositories, is removing this 'install' wrapper, and having the Zaza
    # tests still passing.
    def install(self):
        custom_ppa_dict = {
            'ussuri': 'ppa:openstack-charmers/magnum-ussuri',
            'victoria': 'ppa:openstack-charmers/magnum-victoria',
        }
        ppa = custom_ppa_dict.get(self.application_version)
        if ppa:
            fetch.add_source(ppa, fail_invalid=True)
            fetch.apt_update(fatal=True)
        super().install()

    def get_amqp_credentials(self):
        """Provide the default amqp username and vhost as a tuple.
        :returns (username, host): two strings to send to the amqp provider.
        """
        return (self.config['rabbit-user'], self.config['rabbit-vhost'])

    def get_database_setup(self):
        return [
            dict(
                database=self.config['database'],
                username=self.config['database-user'], )
        ]

    @property
    def local_address(self):
        """Return local address as provided by our ConfigurationClass."""
        return self.configuration_class().local_address

    @property
    def local_unit_name(self):
        """Return local unit name as provided by our ConfigurationClass."""
        return self.configuration_class().local_unit_name
