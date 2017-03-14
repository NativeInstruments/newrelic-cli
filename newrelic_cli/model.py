class ConfigFileError(Exception):
    pass


class ConfigFieldMissingError(ConfigFileError):
    pass


class ScriptFile():
    def __init__(self, dictionary):
        try:
            self.name = dictionary['name']
        except (KeyError, TypeError):
            raise ConfigFieldMissingError("Missing name for the script file.")

        try:
            self.template = dictionary['template']
        except KeyError:
            self.template = None
        supported_templates = ['jinja', None]
        if self.template not in supported_templates:
            raise ConfigFileError(
                "Unsupported template: {}".format(self.template)
            )
        try:
            self.context = dictionary['context']
        except KeyError:
            self.context = {}


class Monitor():
    def __init__(self, label, dictionary):
        self.__dict__ = dictionary

        try:
            self.name = dictionary['name']
        except KeyError:
            self.name = label
        required_fields = ['type', 'frequency', 'locations', 'status']
        missing_fields = []
        for field in required_fields:
            if field not in dictionary:
                missing_fields.append(field)
        if len(missing_fields) > 0:
            raise ConfigFieldMissingError(
                "The following required fields are missing from the config:\n"
                "{}".format('\n'.join(missing_fields))
            )

        if 'script_file' in dictionary:
            self.script_file = ScriptFile(dictionary['script_file'])

        # This fields are optional in config
        #  though it's handy to have same structure for all objects
        if 'slaThreshold' not in dictionary:
            self.slaThreshold = None
        if 'alert_policy' not in dictionary:
            self.alert_policy = None


class AlertPolicy():
    def __init__(self, label, dictionary):
        self.__dict__ = dictionary

        try:
            self.name = dictionary['name']
        except KeyError:
            self.name = label

        # This fields are optional in config
        #  though it's handy to have same structure for all objects
        if 'incident_preference' not in dictionary:
            self.incident_preference = None


class Config():
    def __init__(self, dictionary):
        self.monitors = []
        try:
            monitors = dictionary['monitors']
        except KeyError:
            monitors = {}

        for label, monitor_data in monitors.iteritems():
            monitor = Monitor(label, monitor_data)
            self.monitors.append(monitor)

        self.alert_policies = []
        try:
            alert_policies = dictionary['alert_policies']
        except KeyError:
            alert_policies = {}

        for label, alert_policy_data in alert_policies.iteritems():
            alert_policy = AlertPolicy(label, alert_policy_data)
            self.alert_policies.append(alert_policy)

        try:
            self.context = dictionary['context']
        except KeyError:
            self.context = {}


class Secrets():
    def __init__(self, dictionary):
        try:
            self.api_key = dictionary['api_key']
        except KeyError:
            raise ConfigFieldMissingError(
                "Field api_key is missing from the secrets configuration file"
            )
