import base64

from .base import NewRelicBaseClient
from .exceptions import ItemNotFoundError, NewRelicException


class SyntheticsClient(NewRelicBaseClient):
    def __init__(self, api_key,
                 base_url='https://synthetics.newrelic.com/synthetics/api',
                 timeout=10
                 ):
        super(SyntheticsClient, self).__init__(api_key, base_url, timeout)

    def get_all_monitors(self):
        url = '{}/v3/monitors'.format(self.base_url)
        r = self._get(
            url,
            headers=self.default_headers,
            timeout=self.timeout
        )
        return r.json()['monitors']

    def get_monitor_by_id(self, monitor_id):
        monitors_list = self.get_all_monitors()
        for monitor in monitors_list:
            if monitor['id'] == monitor_id:
                return monitor
        # if not found - return None
        return None

    def get_monitor_by_name(self, name):
        monitors_list = self.get_all_monitors()
        for monitor in monitors_list:
            if monitor['name'] == name:
                return monitor
        # if not found - return None
        return None

    def create_monitor(self, name,
                       type='SCRIPT_API',
                       frequency=30,
                       locations=['AWS_US_WEST_1'],
                       status='DISABLED',
                       slaThreshold=None
                       ):
        """
        Creates a monitor. If creation is successful -
         the monitor object is returned
        """
        url = '{}/v3/monitors'.format(self.base_url)
        payload = {
            'name': name,
            'type': type,
            'frequency': frequency,
            'locations': locations,
            'status': status,
        }
        if slaThreshold:
            payload['slaThreshold'] = slaThreshold

        r = self._post(
            url,
            headers=self.default_headers,
            timeout=self.timeout,
            json=payload
        )
        location = r.headers['location']
        r = self._get(
            location,
            headers=self.default_headers,
            timeout=self.timeout
        )
        return r.json()

    def update_monitor(self, current_name,
                       new_name=None,
                       frequency=None,
                       locations=None,
                       status=None,
                       monitor_type=None,
                       slaThreshold=None
                       ):
        # we will need monitor ID. So get the monitor object first
        monitor = self.get_monitor_by_name(current_name)
        if not monitor:
            raise ItemNotFoundError(
                'Monitor {} not found'.format(current_name)
            )

        payload = {}
        any_changes = False
        if new_name is not None:
            payload['name'] = new_name
            any_changes = True
        else:
            payload['name'] = monitor['name']

        if frequency is not None:
            payload['frequency'] = frequency
            any_changes = True
        else:
            payload['frequency'] = monitor['frequency']

        if locations is not None:
            payload['locations'] = locations
            any_changes = True
        else:
            payload['locations'] = monitor['locations']

        if status is not None:
            payload['status'] = status
            any_changes = True
        else:
            payload['status'] = monitor['status']

        if monitor_type is not None:
            payload['type'] = monitor_type
            any_changes = True
        else:
            payload['type'] = monitor['type']

        if slaThreshold is not None:
            payload['slaThreshold'] = slaThreshold
            any_changes = True
        else:
            payload['slaThreshold'] = monitor['slaThreshold']

        if not any_changes:
            raise NewRelicException('No changes requested.')

        url = '{}/v3/monitors/{}'.format(self.base_url, monitor['id'])
        self._put(
            url,
            headers=self.default_headers,
            timeout=self.timeout,
            json=payload
        )

    def delete_monitor(self, name):
        # we will need monitor ID. So get the monitor object first
        monitor = self.get_monitor_by_name(name)
        if not monitor:
            raise ItemNotFoundError('Monitor {} not found'.format(name))

        url = '{}/v3/monitors/{}'.format(self.base_url, monitor['id'])
        self._delete(
            url,
            headers=self.default_headers,
            timeout=self.timeout
        )

    def get_monitor_script(self, name):
        # we will need monitor ID. So get the monitor object first
        monitor = self.get_monitor_by_name(name)
        if not monitor:
            raise ItemNotFoundError('Monitor {} not found'.format(name))

        url = '{}/v3/monitors/{}/script'.format(self.base_url, monitor['id'])
        try:
            r = self._get(
                url,
                headers=self.default_headers,
                timeout=self.timeout
            )
        # Make error message more specific
        except ItemNotFoundError:
            raise ItemNotFoundError(
                'Script for monitor {} not found'
                .format(name)
            )
        script_base64 = r.json()['scriptText']
        script = base64.b64decode(script_base64)
        return script

    def upload_monitor_script(self, monitor_name, script):
        # we will need monitor ID. So get the monitor object first
        monitor = self.get_monitor_by_name(monitor_name)
        if not monitor:
            raise ItemNotFoundError(
                'Monitor {} not found'.format(monitor_name)
            )
        url = '{}/v3/monitors/{}/script'.format(self.base_url, monitor['id'])
        payload = {'scriptText': base64.b64encode(script)}
        self._put(
            url,
            headers=self.default_headers,
            timeout=self.timeout,
            json=payload
        )
