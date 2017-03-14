import requests

from .exceptions import (ChecksLimitExceeded, ItemNotFoundError,
                         NewRelicException, Timeout, UnathorizedError)


class NewRelicBaseClient(object):
    def __init__(self, api_key, base_url,
                 timeout=10
                 ):
        self.api_key = api_key
        self.base_url = base_url
        # HTTP requests timeout in seconds
        self.timeout = timeout
        self.default_headers = {'X-Api-Key': api_key}

    def _request(self, method, *args, **kwargs):
        """Performs an HTTP request set in 'method'. Returns requests object
        The method will try to catch some of the typical errors and
          gather error messages from Newrelic API
        Each known error has a corresponding exception.
        All exceptions are inherited from generic NewRelicException
        If HTTP return code is not known
          a generic NewRelicException is raised.
        """
        try:
            r = getattr(requests, method)(*args, **kwargs)
        except AttributeError:
            raise NewRelicException(
                'Method {} is unsupported by requests module'
                .format(method)
            )
        except requests.exceptions.Timeout:
            raise Timeout('Request timed out after {} seconds'
                          .format(self.timeout))

        if r.status_code < 200 or r.status_code > 299:
            # Try to work out all known errors into separate exceptions
            if r.status_code == 401:
                try:
                    error_message = r.json()['error']['title']
                except (KeyError, ValueError):
                    raise UnathorizedError(
                        'User is not authorized to perform requested operation'
                    )
                else:
                    raise UnathorizedError(error_message)
            if r.status_code == 402:
                raise ChecksLimitExceeded(
                    "Creating the monitor will increase your scheduled checks "
                    "past your account's purchased check limit."
                )
            elif r.status_code == 404:
                try:
                    error_message = r.json()['error']['title']
                except (KeyError, ValueError):
                    raise ItemNotFoundError(
                        'Requested item not found. '
                        'No error message was provided by server.'
                    )
                else:
                    raise ItemNotFoundError(error_message)
            else:
                # If we don't know what to do with specific error code
                #  ( most likely it's 400 )
                # We at least try to get error message from the response
                try:
                    response_errors = r.json()['errors']
                    raise NewRelicException(
                        "The following errors were returned by server:\n{}"
                        .format('\n'
                                .join(
                                    [x['error'] for x in response_errors]
                                ))
                    )
                # Sometimes API does not return any useful information.
                # In this case that's just an HTML page
                #  reporting 400 instead of JSON.
                # We will just return an error code in this case.
                except ValueError:
                    raise NewRelicException(
                        'Got unexpected response code {}. '
                        'No additional information provided by server.'
                        .format(r.status_code)
                    )
        return r

    def _get(self, *args, **kwargs):
        """Wrapper for requests GET method"""
        return self._request('get', *args, **kwargs)

    def _post(self, *args, **kwargs):
        """Wrapper for requests POST method"""
        return self._request('post', *args, **kwargs)

    def _put(self, *args, **kwargs):
        """Wrapper for requests PUT method"""
        return self._request('put', *args, **kwargs)

    def _delete(self, *args, **kwargs):
        """Wrapper for requests DELETE method"""
        return self._request('delete', *args, **kwargs)
