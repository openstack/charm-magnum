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

import charms_openstack.test_utils as test_utils

import charm.openstack.magnum.magnum as magnum


class Helper(test_utils.PatchHelper):

    def setUp(self):
        super().setUp()
        self.patch('charmhelpers.core.hookenv.is_subordinate',
                   return_value=False)
        self.patch_release(magnum.MagnumCharm.release)


class TestMagnumCharmConfigProperties(Helper):

    def test_magnum_password(self):
        cls = mock.MagicMock()
        self.patch_object(magnum, 'leadership')
        magnum.magnum_password(cls)
        self.leadership.leader_get.assert_called_with('magnum_password')

    def test_ca_file_path(self):
        cls = mock.MagicMock()
        self.patch('os.path.exists', 'exists')
        self.patch('os.path.join', 'ca_cert_file')
        self.ca_cert_file.return_value = '/certs/magnum.crt'
        ca_file = magnum.ca_file_path(cls)
        self.assertEqual('/certs/magnum.crt', ca_file)


class TestMagnumCharm(Helper):

    def setUp(self):
        super().setUp()
        self.target = magnum.MagnumCharm()

    def test_get_amqp_credentials(self):
        cfg_data = {
            "rabbit-user": "magnum",
            "rabbit-vhost": "openstack",
        }
        self.target.config = cfg_data
        result = self.target.get_amqp_credentials()
        self.assertEqual(result, ('magnum', 'openstack'))

    def test_get_database_setup(self):
        cfg_data = {
            "database-user": "magnum",
            "database": "magnum",
        }
        self.target.config = cfg_data
        result = self.target.get_database_setup()
        self.assertEqual(result, [{'database': 'magnum',
                                   'username': 'magnum'}])

    def test_local_address(self):
        configuration_class = mock.MagicMock()
        self.target.configuration_class = configuration_class
        self.assertEqual(self.target.local_address,
                         configuration_class().local_address)

    def test_local_unit_name(self):
        configuration_class = mock.MagicMock()
        self.target.configuration_class = configuration_class
        self.assertEqual(self.target.local_unit_name,
                         configuration_class().local_unit_name)
