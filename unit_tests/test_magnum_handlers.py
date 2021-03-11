# Copyright 2021 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock

import charm.openstack.magnum.magnum as magnum
import reactive.magnum_handlers as handlers

import charms_openstack.test_utils as test_utils


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        defaults = [
            'charm.installed',
            'amqp.connected',
            'shared-db.connected',
            'identity-service.connected',
            'config.changed',
            'update-status',
            'upgrade-charm',
            'certificates.available',
        ]
        hook_set = {
            'when': {
                'render_config': (
                    'shared-db.available',
                    'identity-service.available',
                    'amqp.available',),
                'render_config_with_certs': (
                    'certificates.available',
                    'shared-db.available',
                    'identity-service.available',
                    'amqp.available',),
                'run_db_migration': ('config.complete',),
                'connect_cluster': ('ha.connected',),
                'generate_magnum_password': ('leadership.is_leader',),
                'generate_heartbeat_key': ('leadership.is_leader',),
                'setup_endpoint': ('identity-service.connected',),
                'write_openrc': (
                    'leadership.set.magnum_password',
                    'leadership.is_leader',
                    'identity-service.available',),
            },
            'when_not': {
                'run_db_migration': ('db.synced', 'is-update-status-hook'),
                'connect_cluster': ('ha.available', 'is-update-status-hook'),
                'generate_heartbeat_key': ('leadership.set.heartbeat-key',
                                           'is-update-status-hook'),
                'generate_magnum_password': ('leadership.set.magnum_password',
                                             'is-update-status-hook'),
                'setup_endpoint': ('is-update-status-hook',),
                'render_config': ('is-update-status-hook',),
                'render_config_with_certs': ('is-update-status-hook',),
                'write_openrc': ('is-update-status-hook',),
            },
        }
        # test that the hooks were registered via the
        # reactive.magnum_handlers
        self.registered_hooks_test_helper(handlers, hook_set, defaults)


class TestMagnumHandlers(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch_release(magnum.MagnumCharm.release)
        self.magnum_charm = mock.MagicMock()
        self.patch_object(handlers.charm, 'provide_charm_instance',
                          new=mock.MagicMock())
        self.provide_charm_instance().__enter__.return_value = \
            self.magnum_charm
        self.provide_charm_instance().__exit__.return_value = None

    def test_setup_endpoint(self):
        keystone = mock.MagicMock()
        charm = magnum.MagnumCharm.singleton
        handlers.setup_endpoint(keystone)
        keystone.register_endpoints.assert_called_once_with(
            charm.service_type,
            charm.region,
            '{}/v1'.format(charm.public_url),
            '{}/v1'.format(charm.internal_url),
            '{}/v1'.format(charm.admin_url)
        )

    def test_render_config(self):
        self.patch('charms.reactive.set_state', 'set_state')
        handlers.render_config('arg1', 'arg2')
        self.magnum_charm.render_with_interfaces.assert_called_once_with(
            ('arg1', 'arg2'))
        self.magnum_charm.assess_status.assert_called_once_with()
        self.set_state.assert_called_once_with('config.complete')

    def test_render_config_with_certs(self):
        self.patch('charms.reactive.set_state', 'set_state')
        handlers.render_config_with_certs('arg1', 'arg2', 'arg3', 'arg4')
        self.magnum_charm.configure_tls.assert_called_once_with('arg4')
        self.magnum_charm.render_with_interfaces.assert_called_once_with(
            ['arg1', 'arg2', 'arg3', 'arg4'])
        self.magnum_charm.assess_status.assert_called_once_with()
        self.set_state.assert_called_once_with('config.complete')

    def test_run_db_migration(self):
        self.patch('charms.reactive.set_state', 'set_state')
        handlers.run_db_migration()
        self.magnum_charm.db_sync.assert_called_once_with()
        self.magnum_charm.restart_all.assert_called_once_with()
        self.set_state.assert_called_once_with('db.synced')
        self.magnum_charm.assess_status.assert_called_once_with()

    def test_connect_cluster(self):
        hacluster = mock.MagicMock()
        handlers.connect_cluster(hacluster)
        self.magnum_charm.configure_ha_resources.assert_called_once_with(
            hacluster)
        self.magnum_charm.assess_status.assert_called_once_with()
