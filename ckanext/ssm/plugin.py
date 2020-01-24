# encoding: utf-8
""" SSM Config CKAN extension.
This provides Amazon SSM Parameter Store interpolations into config values.
"""

import re
import six

from logging import getLogger

import boto3
import boto.utils

from ckan.plugins import implements, SingletonPlugin, IConfigurer

LOG = getLogger(__name__)
SSM_PARAMETER_SYNTAX = re.compile(r'[$][{]ssm:(/[-a-zA-Z0-9_./]+)[}]')

class SSMConfigPlugin(SingletonPlugin):
    """Interpolate SSM Parameter Store values into config.
    """
    implements(IConfigurer, inherit=True)

    def update_config(self, config):
        """Replace any values containing SSM references
        """
        region_name = config.get('ckanext.ssm_config.region_name', None)
        if not region_name:
            LOG.info('ckanext.ssm_config.region_name not found; attempting to auto-detect region')
            try:
                region_name = boto.utils.get_instance_identity()['document']['region']
            except Exception:
                LOG.warn("Unable to determine AWS region; please specify 'ckanext.ssm_config.region_name'. Parameters will NOT be interpolated from SSM!")
                return config
        LOG.info('Retrieving SSM parameters from region %s', region_name)
        self.client = boto3.client('ssm', region_name)

        prefix = config.get('ckanext.ssm_config.prefix', None)
        if prefix:
            config = self._populate_config_entries(config, prefix)

        for key in config:
            self._replace_config_value(config, key)
        return config

    def _populate_config_entries(self, config, prefix):
        """Retrieve all SSM parameters under 'prefix' and convert them into config entries.
        """
        if not prefix.endswith('/'):
            prefix += '/'

        LOG.debug('Converting all SSM parameters under %s to config entries', prefix)
        try:
            parameter_names = []
            parameter_search = self.client.describe_parameters(ParameterFilters=[{'Key': 'Path', 'Option': 'Recursive', 'Values': [prefix]}])['Parameters']
            for parameter in parameter_search:
                parameter_names.append(parameter['Name'])
            parameters = self.client.get_parameters(Names=parameter_names, WithDecryption=True)['Parameters']
        except Exception, e:
            LOG.warn("Failed to retrieve parameter tree %s: %s", prefix, e)
            return

        for parameter in parameters:
            config_key = parameter['Name'].replace(prefix, '').replace('/', '.')
            config_value = parameter['Value']
            LOG.debug("Populating %s from SSM", config_key)
            config[config_key] = config_value

    def _replace_config_value(self, config, key):
        """Replace any SSM placeholders in a config entry.
        """
        orig_value = config[key]
        if isinstance(orig_value, six.string_types) and r'${ssm:' in orig_value:
            matches = SSM_PARAMETER_SYNTAX.findall(orig_value)
            new_value = orig_value
            for match in matches:
                LOG.debug('Interpolating SSM parameter %s into entry %s', match, key)
                try:
                    parameter_value = self.client.get_parameter(Name=match, WithDecryption=True)['Parameter']['Value']
                    new_value = new_value.replace(r'${ssm:' + match + '}', parameter_value)
                except Exception, e:
                    LOG.warn("Unable to retrieve %s from SSM: %s", match, e)
            config[key] = new_value
