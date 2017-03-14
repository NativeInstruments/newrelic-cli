from .base import NewRelicBaseClient
from .exceptions import ItemAlreadyExistsError, ItemNotFoundError
from .synthetics import SyntheticsClient


class AlertClient(NewRelicBaseClient):
    def __init__(
        self, api_key,
        base_url='https://api.newrelic.com',
        timeout=10
    ):
        super(AlertClient, self).__init__(api_key, base_url, timeout)

    def get_alert_policies(self, name=None):
        url = '{}/v2/alerts_policies.json'.format(self.base_url)
        if name:
            payload = 'filter[name]={}'.format(name)
            r = self._get(
                url,
                headers=self.default_headers,
                timeout=self.timeout,
                params=payload
            )
        else:
            r = self._get(
                url,
                headers=self.default_headers,
                timeout=self.timeout
            )

        res = r.json()['policies']
        return res

    def create_alert_policy(
        self,
        policy_name,
        incident_preference=None,
        check_unique=True
    ):
        # New Relic API allows creating multiple alerts policies
        #  with the same name. Give a possibility to disallow this in client
        if check_unique:
            policies = self.get_alert_policies(policy_name)
            if len(policies) != 0:
                raise ItemAlreadyExistsError(
                    'Alert policy with name "{}" already exists'
                    .format(policy_name)
                )

        url = '{}/v2/alerts_policies.json'.format(self.base_url)
        payload = {
            'policy': {
                'name': policy_name
            }
        }
        if incident_preference is not None:
            payload['policy']['incident_preference'] = incident_preference

        res = self._post(
            url,
            headers=self.default_headers,
            timeout=self.timeout,
            json=payload
        )
        return res.json()['policy']

    def delete_alert_policy(self, policy_name):
        try:
            policy = self.get_alert_policies(policy_name)[0]
        except IndexError:
            raise ItemNotFoundError(
                'Alert Policy with name "{}" not found'.format(policy_name)
            )
        url = '{}/v2/alerts_policies/{}.json'.format(
            self.base_url, policy['id']
        )

        self._delete(
            url,
            headers=self.default_headers,
            timeout=self.timeout,
        )

    def get_alert_conditions(self, policy_name):
        try:
            policy = self.get_alert_policies(policy_name)[0]
        except IndexError:
            raise ItemNotFoundError(
                'Alert policy with name "{}" not found'.format(policy_name)
            )

        url = '{}/v2/alerts_synthetics_conditions.json'.format(self.base_url)
        payload = 'policy_id={}'.format(policy['id'])
        r = self._get(
            url,
            headers=self.default_headers,
            timeout=self.timeout,
            params=payload
        )
        return r.json()

    def create_synthetics_alert_condition(
        self,
        policy_name,
        condition_name,
        monitor_name,
        runbook_url=None,
        enabled=False,
        check_unique=True
    ):
        try:
            policy = self.get_alert_policies(policy_name)[0]
        except IndexError:
            raise ItemNotFoundError(
                'Alert policy with "{}" not found'.format(policy_name)
            )

        synthetics = SyntheticsClient(self.api_key)
        monitor = synthetics.get_monitor_by_name(monitor_name)
        if not monitor:
            raise ItemNotFoundError(
                'Monitor with name "{}" not found'.format(monitor_name)
            )

        # New Relic API allows creating multiple alerts conditions
        #  from the same monitor using the same alert policy
        #  to avoid creating lots of duplicate entries - disallow this
        if check_unique:
            alert_conditions = self.get_alert_conditions(policy_name)
            # we are only interested in synthetics conditions
            try:
                synth_conditions = alert_conditions['synthetics_conditions']
            except KeyError:
                # we don't have any alert conditions for synthetics
                #  no duplicates then
                pass
            else:
                for condition in synth_conditions:
                    if condition['monitor_id'] == monitor['id']:
                        raise ItemAlreadyExistsError(
                            'Synthetics Alert Condition for monitor "{}" '
                            'is already present in policy "{}" with name "{}"'
                            .format(
                                monitor_name,
                                policy_name,
                                condition['name']
                            )
                        )

        url = (
            '{}/v2/alerts_synthetics_conditions/policies/{}.json'
            .format(self.base_url, policy['id'])
        )
        payload = {
            'synthetics_condition': {
                'name': condition_name,
                'monitor_id': monitor['id'],
                'enabled': enabled
            }
        }
        if runbook_url:
            payload['synthetics_condition']['runbook_url'] = runbook_url

        self._post(
            url,
            headers=self.default_headers,
            timeout=self.timeout,
            json=payload
        )

    def delete_synthetics_alert_conditions(self, policy_name, monitor_name):
        """Deletes all synthetics alert conditions that match pair
        policy_name:monitor_name
        Returns count of conditions deleted
        """
        synthetics = SyntheticsClient(self.api_key)
        monitor = synthetics.get_monitor_by_name(monitor_name)
        if not monitor:
            raise ItemNotFoundError(
                'Monitor with name "{}" not found'.format(monitor_name)
            )

        alert_conditions_deleted = 0
        alert_conditions = self.get_alert_conditions(policy_name)
        # we are only interested in synthetics conditions
        try:
            synthetics_conditions = alert_conditions['synthetics_conditions']
        except KeyError:
            # we don't have any alert conditions for synthetics
            #  no duplicates then
            pass
        else:
            for condition in synthetics_conditions:
                if condition['monitor_id'] == monitor['id']:
                    url = (
                        '{}/v2/alerts_synthetics_conditions/{}.json'
                        .format(self.base_url, condition['id'])
                    )
                    self._delete(
                        url,
                        headers=self.default_headers,
                        timeout=self.timeout
                    )
                    alert_conditions_deleted += 1
        return alert_conditions_deleted
