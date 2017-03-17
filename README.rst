newrelic-cli A Python CLI client and library for New Relic's API
================================================================

.. image:: https://travis-ci.org/NativeInstruments/newrelic-cli.svg?branch=master
    :target: https://travis-ci.org/NativeInstruments/newrelic-cli

newrelic-cli allows setting up your New Relic monitors using simple CLI tool.
Also it provides a set of libraries that can be easily integrated in other
Python projects. It is based on `v3` version of the API when possible,
falling back to `v2` when features are not available in `v3`.


Currently only Synthetics monitors and alerts are supported.

Installation
============

TBD: pip-based installation

To install from the source code::

 $ git clone https://github.com/NativeInstruments/newrelic-cli.git
 $ cd newrelic-cli
 $ python setup.py install

Configuration
=============

secrets
-------
For Synthetics checks newrelic-cli uses NewRelic's Synthetics API.
In order to be able to use it you have to provide admin's API key to the script.
More information on New Relic API keys can be found at:
https://docs.newrelic.com/docs/apis/rest-api-v2/requirements/api-keys

The API key should be stored in the secrets configuration file
in the following format:

.. include:: example/secret.yaml
    :code: yaml

By default newrelic-cli will look for secrets config in the file:
`~/.new_relic/secrets.yaml`. This setting can be overriden with `--secrets-file`
command-line flag

monitors
--------
Configuration of the monitors is stored in the configuration file.
By default newrelic-cli looks up for the `config.yaml` in the current
working directory. This setting can be overriden with `--config-file` or `-c`
command-line arguments.

The configuration file has the following format:

.. include:: example/config.yaml
    :code: yaml

The `monitors` section in the configuration file represents set of monitors.
Each monitor definition starts with a label. Label can be any string and must
be unique. Inside of the definition the following fields are recognized:

 * `name` - optional name of the monitor. Must be unique.
   If not set - a label is used instead.
 * `type` - required monitor type. So far only `SCRIPT_API` is supported
 * `frequency` - required monitor check frequency in minutes. Must be one of 1, 5, 10, 15, 30, 60, 360, 720, or 1440 (this is a limitation on the New Relic side)
 * `locations` - required list of locations for checks.
   Full list of supported locations available in New Relic documentation:
   https://docs.newrelic.com/docs/apis/synthetics-rest-api/monitor-examples/manage-synthetics-monitors-via-rest-api#list-locations
 * `alert_policy` - optional name of the New Relic Alert Policy
   used in case of script failure.
 * `script_file` - required field describing the script file to be used for the monitor

The `context` section of the configuration file contains a YAML dict
with key-value paris. This context will be applied to each template
script file before uploading it.
Values of the global context may be overriden by each script's own context.

script file options
~~~~~~~~~~~~~~~~~~~
 * `name` - required path to the file containing script.
   Can be absolute or relative to the configuration file.
 * `template` - optional templating format used to parse configuration file.
   Currently only `jinja` is supported
 * `context` - optional field containing YAML dict with key-value pairs.
   This context will be applied to the template before uploading it.
   Can contain same keys as global context. In this case values from local context will override global values.

Usage
=====
Python package installs a runnable script called `newrelic-cli`.
Currently the following actions are supported:

 * `upload-monitors` - uploads all monitors described in the configuration file.
   Filter regex limiting scope can be supplied using `--filter` or `-f` options.
 * `delete-monitos` - deletes all monitors that match filter provided in
   `--filter` or `-f` option. By default doesn't match on anything.
 * `list-monitors` - outputs a list of all monitors that are currently present
   on the New Relic. Also supports `--filter` or `-f` options.
