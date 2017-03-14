#!/usr/bin/env python2
from __future__ import absolute_import, print_function

import argparse
import os
import re
import sys

import yaml
from jinja2 import exceptions as jinja_exceptions
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .alerts import AlertClient
from .exceptions import (ItemAlreadyExistsError, ItemNotFoundError,
                         NewRelicException)
from .model import Config, ConfigFieldMissingError, Secrets
from .synthetics import SyntheticsClient
from .version import APP_NAME, __version__


# Shamelessly stolen from StackOverflow
# http://stackoverflow.com/questions/38987
def merge_two_dicts(x, y):
    """Given two dicts, merge them into a new dict as a shallow copy."""
    z = x.copy()
    z.update(y)
    return z


def upload_monitors(api_key, config, filter='.*'):
    """Uploads monitors to New Relic.
    Filter is a regex, if no filters specified - all monitors are uploaded"""
    synth_client = SyntheticsClient(api_key)
    alert_client = AlertClient(api_key)
    filter_re = re.compile('^{}$'.format(filter))
    for monitor in config.monitors:
        if not re.search(filter_re, monitor.name):
            continue

        if synth_client.get_monitor_by_name(monitor.name) is not None:
            print(
                'Monitor with name "{}" already exists, skip creating...'
                .format(monitor.name),
                end=' '
            )
        else:
            print('Creating monitor "{}"...'.format(monitor.name), end=' ')
            synth_client.create_monitor(
                monitor.name,
                monitor.type,
                monitor.frequency,
                monitor.locations,
                monitor.status,
                monitor.slaThreshold
            )

        print('uploading monitor script...', end=' ')
        if monitor.script_file.template == 'jinja':
            env = Environment(
                loader=FileSystemLoader(os.path.abspath(os.curdir)),
                undefined=StrictUndefined
            )
            try:
                template = env.get_template(monitor.script_file.name)
            except jinja_exceptions.TemplateNotFound as e:
                print(
                    'count not open script template for reading!\n'
                    'ERROR: template {} not found.'.format(e)
                )
                continue

            # Template's context should override existing values
            #  set in global context
            context = merge_two_dicts(
                config.context,
                monitor.script_file.context
            )
            script = template.render(context)
        else:
            try:
                with open(monitor.script_file.name, 'r') as f:
                    script = f.read()
            except EnvironmentError as e:
                print(
                    'could not open script file for reading!\n'
                    'ERROR: {}'.format(e)
                )
                continue

        try:
            synth_client.upload_monitor_script(monitor.name, script)
        except NewRelicException as e:
            print("failed!\nERROR: {}".format(e))
            continue

        if monitor.alert_policy is not None:
            print('setting up alert...', end=' ')
            try:
                alert_client.create_synthetics_alert_condition(
                    monitor.alert_policy,
                    monitor.name,
                    monitor.name,
                    enabled=True
                )
            except ItemAlreadyExistsError:
                print('alert is already present, skipping...', end=' ')
        print('done.')


def delete_monitors(api_key, config, filter):
    """Delete monitors from New Relic.
    Deletes all monitors in configuration file that fit filter regex."""
    synth_client = SyntheticsClient(api_key)
    filter_re = re.compile('^{}$'.format(filter))
    for monitor in config.monitors:
        if not re.search(filter_re, monitor.name):
            continue

        print('Deleting monitor "{}"...'.format(monitor.name), end='')
        try:
            synth_client.delete_monitor(monitor.name)
        except ItemNotFoundError:
            print('not found, skipping.')
        else:
            print('done.')


def list_monitors(api_key, filter='.*'):
    """Print monitor details.
    Shows all monitors that fit the filter, by default all are shown"""
    synth_client = SyntheticsClient(api_key)
    filter_re = re.compile('^{}$'.format(filter))
    monitors = synth_client.get_all_monitors()
    for monitor in monitors:
        if not re.search(filter_re, monitor['name']):
            continue

        print("{}:".format(monitor['name']))
        print("  Status: {}".format(monitor['status']))
        print("  Frequency: {}".format(monitor['frequency']))
        print("  Type: {}".format(monitor['type']))
        print("  SLA Threshold: {}".format(monitor['slaThreshold']))
        print(
            "  Locations:\n    {}".
            format('\n    '.join(monitor['locations']))
        )
    return


def upload_alert_policies(api_key, config, filter='.*'):
    alerts_client = AlertClient(api_key)
    alert_policies = config.alert_policies
    filter_re = re.compile('^{}$'.format(filter))
    for alert_policy in alert_policies:
        if not re.search(filter_re, alert_policy.name):
            continue

        print("Creating alert policy: {}...".format(alert_policy.name), end='')
        try:
            alerts_client.create_alert_policy(
                alert_policy.name,
                alert_policy.incident_preference
            )
        except ItemAlreadyExistsError:
            print("policy already exists, skipping.")
        else:
            print("done.")


def delete_alert_policies(api_key, config, filter):
    alerts_client = AlertClient(api_key)
    alert_policies = config.alert_policies
    filter_re = re.compile('^{}$'.format(filter))
    for alert_policy in alert_policies:
        if not re.search(filter_re, alert_policy.name):
            continue

        print("Deleting alert policy: {}...".format(alert_policy.name), end='')
        try:
            alerts_client.delete_alert_policy(alert_policy.name)
        except ItemNotFoundError:
            print('not found, skipping.')
        else:
            print('done.')


def list_alert_policies(api_key, filter='.*'):
    """Print alert policies.
    Shows all alert policies that fit the filter, by default all are shown
    As newrelic's filtering supports only exact match - get all policies
     and filter them on our own
    Also for each policy lists all conditions
    """
    alerts_client = AlertClient(api_key)
    synth_client = SyntheticsClient(api_key)
    filter_re = re.compile('^{}$'.format(filter))
    alert_policies = alerts_client.get_alert_policies()
    for policy in alert_policies:
        if not re.search(filter_re, policy['name']):
            continue

        conditions = alerts_client.get_alert_conditions(policy['name']
                                                        )
        print("{}:".format(policy['name']))
        print("  ID: {}".format(policy['id']))
        print("  Incident Preference: {}".format(
            policy['incident_preference'])
        )
        print("  Coditions:")
        for condition_type in conditions:
            for condition in conditions[condition_type]:
                monitor = synth_client.get_monitor_by_id(
                    condition['monitor_id']
                )
                print("    {}".format(condition['name']))
                print("      ID: {}".format(condition['id']))
                print("      Type: {}".format(condition_type))
                print("      Enabled: {}".format(condition['enabled']))
                try:
                    print("      Monitor ID: {}".format(monitor['name']))
                except TypeError:
                    pass


def get_secrets(source):
    """Reads secrets from YAML config file. Returns secrets object"""
    # Expand ~ to full path
    secrets_dict = yaml.load(source)

    # we need to have at least api_key in secrets
    try:
        secrets = Secrets(secrets_dict)
    except ConfigFieldMissingError as e:
        print('Failed to read values from secrets file: {}'.format(e))
        print('Exiting.')
        sys.exit(1)

    return secrets


def get_config(source):
    """Reads configuration from the YAML file. Returns config object"""
    config_dict = yaml.load(source)

    try:
        config = Config(config_dict)
    except ConfigFieldMissingError as e:
        print('Failed to read values from config file: {}'.format(e))
        print('Exiting.')
        sys.exit(1)

    return config


def main():
    parser = argparse.ArgumentParser(
        add_help=False,
        description=(
            'A New Relic CLI client. '
            'Supports creation and deletion of Sythetic Monitors.'
        )
    )
    parser.add_argument(
        "function",
        nargs="?",
        choices=[
            'upload-monitors',
            'delete-monitors',
            'list-monitors',
            'upload-alert-policies',
            'delete-alert-policies',
            'list-alert-policies'
        ],
        help='Action to perform'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='{} {}'.format(APP_NAME, __version__)
    )

    # Help handling with subcommands is shamelessly stolen from here:
    # http://stackoverflow.com/questions/24584784
    parser.add_argument(
        '--help',
        action='store_true',
        help='show this help message and exit'
    )
    args, sub_args = parser.parse_known_args()

    # Manually handle help
    if args.help:
        # If no subcommand was specified, give general help
        if args.function is None:
            print(parser.format_help())
            sys.exit(1)
        # Otherwise pass the help option on to the subcommand
        sub_args.append('--help')
    else:
        help_message = parser.format_help()

    parser = argparse.ArgumentParser(
        prog="{} {}".
        format(os.path.basename(sys.argv[0]), args.function)
    )

    # Generic arguments that should be added to all subcommands
    secrets_file = os.path.expanduser('~/.new_relic/secret.yaml')
    parser.add_argument(
        '--secrets-file',
        default=secrets_file,
        type=argparse.FileType('r'),
        help=(
            'Secrets file containing New Relic API key. '
            'Defaults to ~/.new_relic/secret.yaml'
        )
    )
    parser.add_argument(
        '--config-file', '-c',
        default='./config.yaml',
        type=argparse.FileType('r'),
        help=(
            'Configuration file containing all monitors. '
            'Defaults to ./config.yaml'
        )
    )
    parser.add_argument(
        '--filter', '-f',
        default='.*',
        help=(
            'Regex to filter items. '
            'By default all items are selected '
            'for upload- and list- operations, '
            'none are selected for delete- operations '
            'Regex is anchored to beginning and end of line. '
            'Surround the regex with .* from both sides to untie it.'
        )
    )

    if args.function == 'upload-monitors':
        args = parser.parse_args(sub_args)
        config = get_config(args.config_file)
        secrets = get_secrets(args.secrets_file)
        # As paths to the script files in config are relative
        #  chdir into cofnig file folder
        os.chdir(os.path.dirname(args.config_file.name))
        upload_monitors(secrets.api_key, config, args.filter)
    elif args.function == 'delete-monitors':
        args = parser.parse_args(sub_args)
        config = get_config(args.config_file)
        secrets = get_secrets(args.secrets_file)
        # As paths to the script files in config are relative
        #  chdir into cofnig file folder
        os.chdir(os.path.dirname(args.config_file.name))
        delete_monitors(secrets.api_key, config, args.filter)
    elif args.function == 'list-monitors':
        args = parser.parse_args(sub_args)
        secrets = get_secrets(args.secrets_file)
        list_monitors(secrets.api_key, args.filter)
    elif args.function == 'upload-alert-policies':
        args = parser.parse_args(sub_args)
        config = get_config(args.config_file)
        secrets = get_secrets(args.secrets_file)
        upload_alert_policies(secrets.api_key, config, args.filter)
    elif args.function == 'delete-alert-policies':
        args = parser.parse_args(sub_args)
        config = get_config(args.config_file)
        secrets = get_secrets(args.secrets_file)
        delete_alert_policies(secrets.api_key, config, args.filter)
    elif args.function == 'list-alert-policies':
        args = parser.parse_args(sub_args)
        secrets = get_secrets(args.secrets_file)
        list_alert_policies(secrets.api_key, args.filter)
    else:
        print("Action or --version required")
        print(help_message)
        sys.exit(1)


if __name__ == '__main__':
    main()
