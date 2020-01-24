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
        for key in config:
            self._replace_config_value(config, key)
        return config

    def _replace_config_value(self, config, key):
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
