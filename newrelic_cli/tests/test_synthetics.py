import base64
from unittest import TestCase

import newrelic_cli.exceptions
from newrelic_cli.synthetics import SyntheticsClient

import requests_mock


@requests_mock.mock()
class NewRelicSyntheticsClientTests(TestCase):
    def setUp(self):
        super(NewRelicSyntheticsClientTests, self).setUp()
        self.client = SyntheticsClient(api_key='dummy_key')

        # Number of pre-cooked values we will use in most of the tests
        self.monitor_name = 'I am a monitor without an alert condition'
        self.monitor_id = 'aff9f4f2-57b9-49de-9f88-83efa059bca4'
        self.first_monitor = {
            'id': self.monitor_id,
            'name': self.monitor_name,
            'type': 'SCRIPT_API',
            'frequency': 10,
            'locations': [
                'AWS_US_WEST_1',
            ],
            'status': 'ENABLED',
            'slaThreshold': 7,
            'options': {},
            "modifiedAt": "2017-01-05T15:51:54.603+0000",
            "createdAt": "2017-01-02T16:33:50.160+0000",
            "userId": 0,
            "apiVersion": "0.4.1"
        }
        self.second_monitor = {
            'id': '4f1ee15f-ed13-47ba-9ab8-6ce1ac27a8ba',
            'name': 'You never need me alone',
            'type': 'SCRIPT_API',
            'frequency': 10,
            'locations': [
                'AWS_US_WEST_1',
            ],
            'status': 'ENABLED',
            'slaThreshold': 7,
            'options': {},
            "modifiedAt": "2017-01-05T15:51:54.603+0000",
            "createdAt": "2017-01-02T16:33:50.160+0000",
            "userId": 0,
            "apiVersion": "0.4.1"
        }
        self.all_monitors_response = {
            'monitors': [
                self.first_monitor,
                self.second_monitor
            ]
        }
        self.monitor_location = '{}/v3/monitors/{}'.format(
            self.client.base_url,
            self.monitor_id
        )
        self.monitor_script_plain = (
            'console.log("Hello, Username!");'
        )
        self.monitor_script_base64 = (
            base64.b64encode(self.monitor_script_plain)
        )

    def test_get_monitor_by_id_success(self, mock):
        monitors_url = '{}/v3/monitors'.format(self.client.base_url)
        mock.get(
            url=monitors_url,
            status_code=200,
            json=self.all_monitors_response
        )
        res = self.client.get_monitor_by_id(self.first_monitor['id'])
        self.assertDictEqual(self.first_monitor, res)

    def test_get_nonexistent_monitor_by_id(self, mock):
        response = {'monitors': []}
        monitors_url = '{}/v3/monitors'.format(self.client.base_url)
        mock.get(
            url=monitors_url,
            status_code=200,
            json=response
        )
        res = self.client.get_monitor_by_id(self.first_monitor['id'])
        self.assertIsNone(res)

    def test_create_monitor_success(self, mock):
        create_monitor_endpoint = '{}/v3/monitors'.format(self.client.base_url)

        mock.post(
            url=create_monitor_endpoint,
            status_code=201,
            headers={'Location': self.monitor_location}
        )
        mock.get(
            url=self.monitor_location,
            status_code=200,
            json=self.first_monitor
        )
        r = self.client.create_monitor(self.monitor_name)
        self.assertDictEqual(r, self.first_monitor)

    def test_create_monitor_with_sla_success(self, mock):
        create_monitor_endpoint = '{}/v3/monitors'.format(self.client.base_url)
        monitor_data = self.first_monitor
        monitor_data['slaThreshold'] = 42

        mock.post(
            url=create_monitor_endpoint,
            status_code=201,
            headers={'Location': self.monitor_location}
        )
        mock.get(
            url=self.monitor_location,
            status_code=200,
            json=monitor_data
        )
        r = self.client.create_monitor(self.monitor_name, slaThreshold=42)
        self.assertDictEqual(r, self.first_monitor)

    def test_update_nonexistent_monitor(self, mock):
        get_all_monitors_endpoint = '{}/v3/monitors'.format(
            self.client.base_url
        )
        monitor_endpooint = '{}/v3/monitors/{}'.format(
            self.client.base_url,
            self.monitor_id
        )
        # we don't have any monitors
        monitors_list = {'monitors': []}
        mock.get(
            url=get_all_monitors_endpoint,
            status_code=200,
            json=monitors_list
        )
        mock.put(
            url=monitor_endpooint,
            status_code=204
        )
        # we don't need any more endpoints
        with self.assertRaisesRegexp(
                newrelic_cli.exceptions.ItemNotFoundError,
                '{}'.format(self.monitor_name)
        ):
            self.client.update_monitor(
                current_name=self.monitor_name,
                new_name='I am changed name'
            )

    def test_update_monitor_name(self, mock):
        get_all_monitors_endpoint = '{}/v3/monitors'.format(
            self.client.base_url
        )
        monitor_endpooint = '{}/v3/monitors/{}'.format(
            self.client.base_url,
            self.monitor_id
        )
        mock.put(
            url=monitor_endpooint,
            status_code=204
        )
        mock.get(
            url=get_all_monitors_endpoint,
            status_code=200,
            json=self.all_monitors_response
        )
        mock.get(
            url=self.monitor_location,
            status_code=200,
            json=self.first_monitor
        )
        # We don't expect any response here.
        # Just make sure no exceptions raised
        self.client.update_monitor(
            current_name=self.monitor_name,
            new_name='I am changed name'
        )

    def test_update_monitor_everything_but_name(self, mock):
        get_all_monitors_endpoint = '{}/v3/monitors'.format(
            self.client.base_url
        )
        monitor_endpooint = '{}/v3/monitors/{}'.format(
            self.client.base_url,
            self.monitor_id
        )
        mock.put(
            url=monitor_endpooint,
            status_code=204
        )
        mock.get(
            url=get_all_monitors_endpoint,
            status_code=200,
            json=self.all_monitors_response
        )
        mock.get(
            url=self.monitor_location,
            status_code=200,
            json=self.first_monitor
        )
        # We don't expect any response here.
        # Just make sure no exceptions raised
        self.client.update_monitor(
            self.monitor_name,
            frequency=42,
            locations=['AWS_US_EAST_1'],
            status='DISABLED',
            monitor_type='SIMPLE',
            slaThreshold=8
        )

    def test_update_monitor_no_changes(self, mock):
        get_all_monitors_endpoint = '{}/v3/monitors'.format(
            self.client.base_url
        )
        monitor_endpooint = '{}/v3/monitors/{}'.format(
            self.client.base_url,
            self.monitor_id
        )
        mock.put(
            url=monitor_endpooint,
            status_code=204
        )
        mock.get(
            url=get_all_monitors_endpoint,
            status_code=200,
            json=self.all_monitors_response
        )
        mock.get(
            url=self.monitor_location,
            status_code=200,
            json=self.first_monitor
        )
        with self.assertRaisesRegexp(
                newrelic_cli.exceptions.NewRelicException,
                'No changes requested.'
        ):
            self.client.update_monitor(
                current_name=self.monitor_name
            )

    def test_delete_monitor_success(self, mock):
        get_all_monitors_endpoint = '{}/v3/monitors'.format(
            self.client.base_url
        )
        monitor_endpooint = '{}/v3/monitors/{}'.format(
            self.client.base_url,
            self.monitor_id
        )
        mock.get(
            url=get_all_monitors_endpoint,
            status_code=200,
            json=self.all_monitors_response
        )
        mock.delete(
            url=monitor_endpooint,
            status_code=204
        )
        # We don't expect any response here.
        # Just make sure no exceptions raised
        self.client.delete_monitor(self.monitor_name)

    def test_delete_nonexistent_monitor(self, mock):
        get_all_monitors_endpoint = '{}/v3/monitors'.format(
            self.client.base_url
        )
        monitor_endpooint = '{}/v3/monitors/{}'.format(
            self.client.base_url,
            self.monitor_id
        )
        # we don't have any monitors
        monitors_list = {'monitors': []}

        mock.get(
            url=get_all_monitors_endpoint,
            status_code=200,
            json=monitors_list
        )
        mock.delete(
            url=monitor_endpooint,
            status_code=204
        )
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.ItemNotFoundError,
            '{}'.format(self.monitor_name)
        ):
            self.client.delete_monitor(self.monitor_name)

    def test_get_monitor_script_success(self, mock):
        get_all_monitors_endpoint = '{}/v3/monitors'.format(
            self.client.base_url
        )
        monitor_script_endpoint = '{}/v3/monitors/{}/script'.format(
            self.client.base_url,
            self.monitor_id
        )
        mock.get(
            url=get_all_monitors_endpoint,
            status_code=200,
            json=self.all_monitors_response
        )
        mock.get(
            url=monitor_script_endpoint,
            status_code=200,
            json={'scriptText': self.monitor_script_base64}
        )
        script = self.client.get_monitor_script(self.monitor_name)
        self.assertEquals(self.monitor_script_plain, script)

    def test_get_nonexistent_monitor_script(self, mock):
        get_all_monitors_endpoint = '{}/v3/monitors'.format(
            self.client.base_url
        )
        monitor_script_endpoint = '{}/v3/monitors/{}/script'.format(
            self.client.base_url,
            self.monitor_id
        )
        # we don't have any monitors
        monitors_list = {'monitors': []}

        mock.get(
            url=get_all_monitors_endpoint,
            status_code=200,
            json=monitors_list
        )
        mock.get(
            url=monitor_script_endpoint,
            status_code=200,
            json={'scriptText': self.monitor_script_base64}
        )
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.ItemNotFoundError,
            '{}'.format(self.monitor_name)
        ):
            self.client.get_monitor_script(self.monitor_name)

    def test_get_monitor_without_script(self, mock):
        get_all_monitors_endpoint = '{}/v3/monitors'.format(
            self.client.base_url
        )
        monitor_script_endpoint = '{}/v3/monitors/{}/script'.format(
            self.client.base_url,
            self.monitor_id
        )
        mock.get(
            url=get_all_monitors_endpoint,
            status_code=200,
            json=self.all_monitors_response
        )
        mock.get(
            url=monitor_script_endpoint,
            status_code=404,
        )
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.ItemNotFoundError,
            '{}'.format(self.monitor_name)
        ):
            self.client.get_monitor_script(self.monitor_name)

    def test_upload_monitor_script_success(self, mock):
        get_all_monitors_endpoint = '{}/v3/monitors'.format(
            self.client.base_url
        )
        monitor_script_endpoint = '{}/v3/monitors/{}/script'.format(
            self.client.base_url,
            self.monitor_id
        )
        mock.get(
            url=get_all_monitors_endpoint,
            status_code=200,
            json=self.all_monitors_response
        )
        mock.put(
            url=monitor_script_endpoint,
            status_code=204
        )
        # We don't expect any response here.
        # Just make sure no exceptions raised
        self.client.upload_monitor_script(
            self.monitor_name,
            self.monitor_script_plain
        )

    def test_upload_nonexistent_monitor_script(self, mock):
        get_all_monitors_endpoint = '{}/v3/monitors'.format(
            self.client.base_url
        )
        monitor_script_endpoint = '{}/v3/monitors/{}/script'.format(
            self.client.base_url,
            self.monitor_id
        )
        # we don't have any monitors
        monitors_list = {'monitors': []}

        mock.get(
            url=get_all_monitors_endpoint,
            status_code=200,
            json=monitors_list
        )
        mock.put(
            url=monitor_script_endpoint,
            status_code=204
        )
        # We don't expect any response here.
        # Just make sure no exceptions raised
        with self.assertRaisesRegexp(
                newrelic_cli.exceptions.ItemNotFoundError,
                '{}'.format(self.monitor_name)
        ):
            self.client.upload_monitor_script(
                self.monitor_name,
                self.monitor_script_plain
            )
