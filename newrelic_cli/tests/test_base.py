from unittest import TestCase

import newrelic_cli.exceptions
from newrelic_cli.base import NewRelicBaseClient
from requests.exceptions import Timeout

import requests_mock


@requests_mock.mock()
class NewRelicBaseClientTests(TestCase):
    def setUp(self):
        super(NewRelicBaseClientTests, self).setUp()
        self.client = NewRelicBaseClient(
            api_key='dummy_key',
            base_url='https://api.newrelic.com'
        )

    def test_get_success(self, mock):
        url = '{}/v2/get_me'.format(self.client.base_url)
        mock.get(url=url)
        r = self.client._get(url)
        self.assertEquals(r.status_code, 200)

    def test_post_success(self, mock):
        url = '{}/v2/post_me'.format(self.client.base_url)
        mock.post(url=url, status_code=200)
        r = self.client._post(url)
        self.assertEquals(r.status_code, 200)

    def test_put(self, mock):
        url = '{}/v2/put_me'.format(self.client.base_url)
        mock.put(url=url, status_code=200)
        r = self.client._put(url)
        self.assertEquals(r.status_code, 200)

    def test_delete(self, mock):
        url = '{}/v2/delete_me'.format(self.client.base_url)
        mock.delete(url=url, status_code=200)
        r = self.client._delete(url)
        self.assertEquals(r.status_code, 200)

    def test_invalid_method(self, mock):
        url = '{}/v2/eat_me'.format(self.client.base_url)
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.NewRelicException,
            'Method \w+ is unsupported by requests module'

        ):
            self.client._request(method='eat', url=url)

    # As _get, _post, _put and _delete methods don't do anything on their own
    #  we just test all cases with _get and assume that others behave the same
    def test_get_payment_required(self, mock):
        url = '{}/v2/take_my_money.json'.format(self.client.base_url)
        mock.get(url=url, status_code=402)
        with self.assertRaises(newrelic_cli.exceptions.ChecksLimitExceeded):
            self.client._get(url)

    def test_get_not_found_with_message(self, mock):
        url = '{}/v2/i_am_not_here.json'.format(self.client.base_url)
        mock.get(
            url=url,
            status_code=404,
            json={'error': {'title': 'I am error message'}}
        )
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.ItemNotFoundError,
            'I am error message'
        ):
            self.client._get(url)

    def test_get_not_found_without_message(self, mock):
        url = '{}/v2/i_am_not_here.json'.format(self.client.base_url)
        mock.get(url=url, status_code=404)
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.ItemNotFoundError,
            '.*?No error message was provided by server\.'
        ):
            self.client._get(url)

    def test_get_unauthorized_item_with_message(self, mock):
        url = '{}/v2/i_am_not_here.json'.format(self.client.base_url)
        mock.get(
            url=url,
            status_code=401,
            json={'error': {'title': 'You shall not pass!'}}
        )
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.UnathorizedError,
            'You shall not pass!'
        ):
            self.client._get(url)

    def test_get_unauthorized_item_without_message(self, mock):
        url = '{}/v2/i_am_here'.format(self.client.base_url)
        mock.get(url=url, status_code=401)
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.UnathorizedError,
            'User is not authorized to perform requested operation'
        ):
            self.client._get(url)

    def test_get_other_error_with_message(self, mock):
        url = '{}/v2/i_am_bogus'.format(self.client.base_url)
        mock.get(
            url=url,
            status_code=400,
            json={
                'errors': [
                    {'error': 'I am bogus'},
                    {'error': 'I am verbose'}
                ]
            }
        )
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.NewRelicException,
            'The following errors were returned by server'
        ):
            self.client._get(url)

    def test_get_other_error_without_message(self, mock):
        url = '{}/v2/i_am_bogus_and_silent'.format(self.client.base_url)
        mock.get(url=url, status_code=400)
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.NewRelicException,
            'Got unexpected response code 400'
        ):
            self.client._get(url)

    def test_get_timeout(self, mock):
        url = '{}/v2/i_dont_respond'.format(self.client.base_url)
        mock.get(url=url, exc=Timeout)
        with self.assertRaisesRegexp(
            newrelic_cli.exceptions.Timeout,
            'Request timed out after \d+ seconds'
        ):
            self.client._get(url)
