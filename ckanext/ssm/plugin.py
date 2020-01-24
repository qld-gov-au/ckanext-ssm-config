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
        if not self._make_client(config):
            LOG.warn("Failed to configure SSM client. Parameters will NOT be interpolated from SSM!")
            return config
        prefix = config.get('ckanext.ssm_config.prefix', None)
        if prefix:
            self._populate_config_entries(config, prefix)

        for key in config:
            self._replace_config_value(config, key)
        return config


    def _make_client(self, config):
        """Construct a Boto3 client for talking to SSM Parameter Store
        """
        region_name = config.get('ckanext.ssm_config.region_name', None)
        access_key = config.get('ckanext.ssm_config.aws_access_key_id', None)
        secret_key = config.get('ckanext.ssm_config.aws_secret_access_key', None)

        if not region_name:
            LOG.debug('ckanext.ssm_config.region_name not found; attempting to auto-detect region')
            try:
                region_name = boto.utils.get_instance_identity()['document']['region']
            except Exception:
                LOG.warn("Unable to determine AWS region; please specify 'ckanext.ssm_config.region_name'.")
                return False

        LOG.info('Retrieving SSM parameters from region %s', region_name)
        try:
            self.client = boto3.client('ssm', region_name, aws_access_key_id=access_key,
                                        aws_secret_access_key=secret_key)
            return self.client
        except Exception, e:
            LOG.error('Failed to initialise SSM Parameter Store client: %s', e)
            return False


    def _populate_config_entries(self, config, prefix):
        """Retrieve all SSM parameters under 'prefix' and convert them into config entries.
        """
        if not prefix.endswith('/'):
            prefix += '/'

        LOG.debug('Converting all SSM parameters under %s to config entries', prefix)
        try:
            parameters = self.client.get_parameters_by_path(Path=prefix, Recursive=True, WithDecryption=True)['Parameters']
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
