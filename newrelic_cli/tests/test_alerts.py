from unittest import TestCase

import newrelic_cli.exceptions
from newrelic_cli.alerts import AlertClient

import requests_mock


@requests_mock.mock()
class NewRelicAlertClientTests(TestCase):
    def setUp(self):
        super(NewRelicAlertClientTests, self).setUp()
        self.client = AlertClient(api_key='dummy_key')

        # Number of pre-cooked values we will use in most of the tests
        self.policy_name = 'DummyPolicy'
        self.policy_id = 1
        self.condition_id = 123456
        self.monitor_name = 'I am a monitor without an alert condition'
        self.monitor_id = 'aff9f4f2-57b9-49de-9f88-83efa059bca4'
        self.first_policy = {
            'id': self.policy_id,
            'incident_preference': 'PER_POLICY',
            'name': self.policy_name,
            'created_at': 1234567890123,
            'updated_at': 1234567890123
        }
        self.second_policy = {
            'id': 2,
            'incident_preference': 'PER_POLICY',
            'name': 'You will never call my name',
            'created_at': 1234567890345,
            'updated_at': 1234567890345
        }
        self.policy_response = {
            'policies': [
                self.first_policy,
                self.second_policy
            ]
        }
        self.conditions_response = {
            'synthetics_conditions': [
                {
                    'id': self.condition_id,
                    'name': self.monitor_name,
                    'monitor_id': self.monitor_id,
                    'enabled': True
                }
            ]
        }
        self.monitor_response = {
            'monitors': [
                {
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
            ]
        }

    def test_get_alert_policies_success(self, mock):
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )
        res = self.client.get_alert_policies()
        self.assertListEqual(self.policy_response['policies'], res)

    def test_get_alert_policy_by_name_success(self, mock):
        response = {
            'policies': [
                self.first_policy
            ]
        }
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=response,
            status_code=200
        )
        res = self.client.get_alert_policies(self.first_policy['name'])
        self.assertDictEqual(self.policy_response['policies'][0], res[0])

    def test_get_nonexistent_alert_policy_by_name(self, mock):
        name = 'NotFoundPolicy'
        response = {
            'policies': []
        }
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=response,
            status_code=200
        )
        res = self.client.get_alert_policies(name)
        self.assertListEqual(response['policies'], res)

    def test_get_alert_condition_success(self, mock):
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )
        mock.get(
            '{}/v2/alerts_synthetics_conditions.json?policy_id={}'
            .format(self.client.base_url, self.policy_id),
            json=self.conditions_response,
            status_code=200
        )

        res = self.client.get_alert_conditions(self.policy_name)
        self.assertDictEqual(res, self.conditions_response)

    def test_get_nonexistent_alert_condition(self, mock):
        policy_name = 'IAmNotHerePolicy'
        policies_response = {
            'policies': []
        }
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=policies_response,
            status_code=200
        )
        # we don't even need a second endpoint here
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.ItemNotFoundError,
            '{}'.format(policy_name)
        ):
            self.client.get_alert_conditions(policy_name)

    def test_create_unique_synthetics_alert_condition_success(self, mock):
        # Alerts policies list mock
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )

        # Alerts conditions endpoint mock with empty list of conditions
        conditions_response = {
            "synthetics_conditions": []
        }
        mock.get(
            '{}/v2/alerts_synthetics_conditions.json?policy_id={}'
            .format(self.client.base_url, self.policy_id),
            json=conditions_response,
            status_code=200
        )

        # Synthetics monitors list mock
        mock.get(
            'https://synthetics.newrelic.com/synthetics/api/v3/monitors',
            status_code=200,
            json=self.monitor_response
        )

        # Alerts policies creation mock
        mock.post(
            '{}/v2/alerts_synthetics_conditions/policies/{}.json'
            .format(self.client.base_url, self.policy_id),
            status_code=201
        )

        # We don't expect any response here.
        # Just make sure no exceptions raised
        self.client.create_synthetics_alert_condition(
            policy_name=self.policy_name,
            condition_name=self.monitor_name,
            monitor_name=self.monitor_name
        )

    def test_create_unique_synthetics_alert_codtition_with_sla_success(
        self,
        mock
    ):
        # Alerts policies list mock
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )

        # Alerts conditions endpoint mock with empty list of conditions
        conditions_response = {
            "synthetics_conditions": []
        }
        mock.get(
            '{}/v2/alerts_synthetics_conditions.json?policy_id={}'
            .format(self.client.base_url, self.policy_id),
            json=conditions_response,
            status_code=200
        )

        # Synthetics monitors list mock
        mock.get(
            'https://synthetics.newrelic.com/synthetics/api/v3/monitors',
            status_code=200,
            json=self.monitor_response
        )

        # Alerts policies creation mock
        mock.post(
            '{}/v2/alerts_synthetics_conditions/policies/{}.json'
            .format(self.client.base_url, self.policy_id),
            status_code=201
        )

        # We don't expect any response here.
        # Just make sure no exceptions raised
        self.client.create_synthetics_alert_condition(
            policy_name=self.policy_name,
            condition_name=self.monitor_name,
            monitor_name=self.monitor_name,
            runbook_url='http://example.com'
        )

    def test_create_unique_synthetics_alert_codtition_empty_response_success(
        self,
        mock
    ):
        # Alerts policies list mock
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )

        # Alerts conditions endpoint mock with empty list of conditions
        conditions_response = {}
        mock.get(
            '{}/v2/alerts_synthetics_conditions.json?policy_id={}'
            .format(self.client.base_url, self.policy_id),
            json=conditions_response,
            status_code=200
        )

        # Synthetics monitors list mock
        mock.get(
            'https://synthetics.newrelic.com/synthetics/api/v3/monitors',
            status_code=200,
            json=self.monitor_response
        )

        # Alerts policies creation mock
        mock.post(
            '{}/v2/alerts_synthetics_conditions/policies/{}.json'
            .format(self.client.base_url, self.policy_id),
            status_code=201
        )

        # We don't expect any response here.
        # Just make sure no exceptions raised
        self.client.create_synthetics_alert_condition(
            policy_name=self.policy_name,
            condition_name=self.monitor_name,
            monitor_name=self.monitor_name,
            runbook_url='http://example.com'
        )

    def test_create_non_unique_synthetics_alert_condition_success(self, mock):
        # Alerts policies list mock
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )
        # Alerts conditions endpoint mock
        mock.get(
            '{}/v2/alerts_synthetics_conditions.json?policy_id={}'
            .format(self.client.base_url, self.policy_id),
            json=self.conditions_response,
            status_code=200
        )
        # Synthetics monitors list mock
        mock.get(
            'https://synthetics.newrelic.com/synthetics/api/v3/monitors',
            status_code=200,
            json=self.monitor_response
        )
        # Alerts policies creation mock
        mock.post(
            '{}/v2/alerts_synthetics_conditions/policies/{}.json'
            .format(self.client.base_url, self.policy_id),
            status_code=201
        )
        # We don't expect any response here.
        # Just make sure no exceptions raised
        self.client.create_synthetics_alert_condition(
            policy_name=self.policy_name,
            condition_name=self.monitor_name,
            monitor_name=self.monitor_name,
            check_unique=False
        )

    def test_create_non_unique_synthetics_alert_condition_fail(self, mock):
        # Alerts policies list mock
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )
        # Alerts conditions endpoint mock
        mock.get(
            '{}/v2/alerts_synthetics_conditions.json?policy_id={}'
            .format(self.client.base_url, self.policy_id),
            json=self.conditions_response,
            status_code=200
        )
        # Synthetics monitors list mock
        mock.get(
            'https://synthetics.newrelic.com/synthetics/api/v3/monitors',
            status_code=200,
            json=self.monitor_response
        )
        # Alerts policies creation mock
        mock.post(
            '{}/v2/alerts_synthetics_conditions/policies/{}.json'
            .format(self.client.base_url, self.policy_id),
            status_code=201
        )
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.ItemAlreadyExistsError,
            'Condition for monitor "{}" .*? in policy "{}" with name "{}"'
            .format(self.monitor_name, self.policy_name, self.monitor_name)
        ):
            self.client.create_synthetics_alert_condition(
                policy_name=self.policy_name,
                condition_name=self.monitor_name,
                monitor_name=self.monitor_name,
            )

    def test_create_synthetics_alert_condition_no_policy(self, mock):
        # Alerts policies list mock
        response = {
            'policies': []
        }
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=response,
            status_code=200
        )
        # We don't need other endpoints
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.ItemNotFoundError,
            '{}'.format(self.policy_name)
        ):
            self.client.create_synthetics_alert_condition(
                policy_name=self.policy_name,
                condition_name=self.monitor_name,
                monitor_name=self.monitor_name,
            )

    def test_create_synthetics_alert_condition_no_monitor(self, mock):
        # Alerts policies list mock
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )
        # Synthetics monitors list mock
        response = {
            'monitors': []
        }
        mock.get(
            'https://synthetics.newrelic.com/synthetics/api/v3/monitors',
            status_code=200,
            json=response
        )
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.ItemNotFoundError,
            '{}'.format(self.monitor_name)
        ):
            self.client.create_synthetics_alert_condition(
                policy_name=self.policy_name,
                condition_name=self.monitor_name,
                monitor_name=self.monitor_name,
            )

    def test_delete_synthetics_alert_condition_success(self, mock):
        # Synthetics monitors list mock
        mock.get(
            'https://synthetics.newrelic.com/synthetics/api/v3/monitors',
            status_code=200,
            json=self.monitor_response
        )
        # Alerts policies list mock
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )
        # Alerts conditions list endpoint mock
        mock.get(
            '{}/v2/alerts_synthetics_conditions.json?policy_id={}'
            .format(self.client.base_url, self.policy_id),
            json=self.conditions_response,
            status_code=200
        )
        # Alerts conditions delete endpoint mock
        mock.delete(
            '{}/v2/alerts_synthetics_conditions/{}.json'
            .format(self.client.base_url, self.condition_id),
            status_code=200
        )
        deleted_conditions = self.client.delete_synthetics_alert_conditions(
            policy_name=self.policy_name,
            monitor_name=self.monitor_name
        )
        self.assertEquals(deleted_conditions, 1)

    def test_delete_synthetics_alert_condition_empty_response_success(
            self,
            mock
    ):
        # Synthetics monitors list mock
        mock.get(
            'https://synthetics.newrelic.com/synthetics/api/v3/monitors',
            status_code=200,
            json=self.monitor_response
        )
        # Alerts policies list mock
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )

        # Alerts conditions endpoint mock with empty list of conditions
        conditions_response = {}
        mock.get(
            '{}/v2/alerts_synthetics_conditions.json?policy_id={}'
            .format(self.client.base_url, self.policy_id),
            json=conditions_response,
            status_code=200
        )
        # Alerts conditions delete endpoint mock
        mock.delete(
            '{}/v2/alerts_synthetics_conditions/{}.json'
            .format(self.client.base_url, self.condition_id),
            status_code=200
        )
        deleted_conditions = self.client.delete_synthetics_alert_conditions(
            policy_name=self.policy_name,
            monitor_name=self.monitor_name
        )
        self.assertEquals(deleted_conditions, 0)

    def test_delete_synthetics_alert_condition_no_policy(self, mock):
        response = {
            'policies': []
        }
        # Synthetics monitors list mock
        mock.get(
            'https://synthetics.newrelic.com/synthetics/api/v3/monitors',
            status_code=200,
            json=self.monitor_response
        )
        # Alerts policies list mock
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=response,
            status_code=200
        )
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.ItemNotFoundError,
            '{}'.format(self.policy_name)
        ):
            self.client.delete_synthetics_alert_conditions(
                policy_name=self.policy_name,
                monitor_name=self.monitor_name,
            )

    def test_delete_synthetics_alert_condition_no_monitor(self, mock):
        response = {
            'monitors': []
        }
        # Synthetics monitors list mock
        mock.get(
            'https://synthetics.newrelic.com/synthetics/api/v3/monitors',
            status_code=200,
            json=response
        )
        # Alerts policies list mock
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.ItemNotFoundError,
            '{}'.format(self.monitor_name)
        ):
            self.client.delete_synthetics_alert_conditions(
                policy_name=self.policy_name,
                monitor_name=self.monitor_name,
            )

    def test_delete_synthetics_alert_condition_no_condition(self, mock):
        # Synthetics monitors list mock
        mock.get(
            'https://synthetics.newrelic.com/synthetics/api/v3/monitors',
            status_code=200,
            json=self.monitor_response
        )
        # Alerts policies list mock
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )
        # Alerts conditions list endpoint mock
        response = {
            'synthetics_conditions': []
        }
        mock.get(
            '{}/v2/alerts_synthetics_conditions.json?policy_id={}'
            .format(self.client.base_url, self.policy_id),
            json=response,
            status_code=200
        )
        # Alerts conditions delete endpoint mock
        mock.delete(
            '{}/v2/alerts_synthetics_conditions/{}.json'
            .format(self.client.base_url, self.condition_id),
            status_code=200
        )
        deleted_conditions = self.client.delete_synthetics_alert_conditions(
            policy_name=self.policy_name,
            monitor_name=self.monitor_name
        )
        self.assertEquals(deleted_conditions, 0)

    def test_create_alert_policy_success(self, mock):
        # Now we don't have any policies
        response = {
            'policies': []
        }
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=response,
            status_code=200
        )
        # Policy created successfully
        policy_created_response = {
            'policy': self.first_policy
        }
        mock.post(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=policy_created_response,
            status_code=201
        )

        created_policy = self.client.create_alert_policy(
            self.first_policy['name']
        )
        self.assertDictEqual(created_policy, self.first_policy)

    def test_create_alert_policy_with_incident_preference(self, mock):
        # Now we don't have any policies
        response = {
            'policies': []
        }
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=response,
            status_code=200
        )
        # Policy created successfully
        policy_created_response = {
            'policy': self.first_policy
        }
        mock.post(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=policy_created_response,
            status_code=201
        )

        created_policy = self.client.create_alert_policy(
            self.first_policy['name'],
            incident_preference=self.first_policy['incident_preference']
        )
        self.assertDictEqual(created_policy, self.first_policy)

    def test_create_alert_policy_duplicate_success(self, mock):
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )
        # Policy already exist
        policy_created_response = {
            'policy': self.first_policy
        }
        mock.post(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=policy_created_response,
            status_code=201
        )
        created_policy = self.client.create_alert_policy(
            self.first_policy['name'],
            check_unique=False
        )
        self.assertDictEqual(created_policy, self.first_policy)

    def test_create_alert_policy_duplicate_failure(self, mock):
        mock.get(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=self.policy_response,
            status_code=200
        )
        # Policy already exist
        policy_created_response = {
            'policy': self.first_policy
        }
        mock.post(
            '{}/v2/alerts_policies.json'.format(self.client.base_url),
            json=policy_created_response,
            status_code=201
        )
        with self.assertRaisesRegexp(
                newrelic_cli.exceptions.ItemAlreadyExistsError,
                '{}'.format(self.first_policy['name'])
        ):
            self.client.create_alert_policy(self.first_policy['name'])

    def test_delete_alert_policy_success(self, mock):
        mock.get(
            '{}/v2/alerts_policies.json?filter[name]={}'
            .format(self.client.base_url, self.first_policy['name']),
            json=self.policy_response,
            status_code=200
        )
        mock.delete(
            '{}/v2/alerts_policies/{}.json'
            .format(self.client.base_url, self.first_policy['id'])
        )
        # Just make sure no exceptions raised
        self.client.delete_alert_policy(self.first_policy['name'])

    def test_delete_nonexistent_alert_policy(self, mock):
        # Now we don't have any policies
        response = {
            'policies': []
        }
        mock.get(
            '{}/v2/alerts_policies.json?filter[name]={}'
            .format(self.client.base_url, self.first_policy['name']),
            json=response,
            status_code=200
        )
        mock.delete(
            '{}/v2/alerts_policies/{}.json'
            .format(self.client.base_url, self.first_policy['id'])
        )
        with self.assertRaisesRegexp(
                newrelic_cli.exceptions.ItemNotFoundError,
                '{}'.format(self.first_policy['name'])
        ):
            self.client.delete_alert_policy(self.first_policy['name'])
