# encoding: utf-8
""" SSM Config CKAN extension.
This provides Amazon SSM Parameter Store interpolations into config values.
"""

import re
import requests
import six

from logging import getLogger

import boto3

from ckan.plugins import implements, SingletonPlugin, IConfigurer

LOG = getLogger(__name__)
SSM_PARAMETER_SYNTAX = re.compile(r'[$][{]ssm:(/[-a-zA-Z0-9_./]+)[}]')


def get_instance_identity_document():
    token = requests.put(
        'http://169.254.169.254/latest/api/token',
        headers={'X-aws-ec2-metadata-token-ttl-seconds': '60'}
    ).text
    return requests.get(
        'http://169.254.169.254/latest/dynamic/instance-identity/document',
        headers={'X-aws-ec2-metadata-token': token}
    ).json()


class SSMConfigPlugin(SingletonPlugin):
    """Interpolate SSM Parameter Store values into config.
    """
    implements(IConfigurer, inherit=True)

    def update_config(self, config):
        """Replace any values containing SSM references
        """
        if not self._make_client(config):
            LOG.warn("""Failed to configure SSM client.
            Parameters will NOT be interpolated from SSM!""")
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
        secret_key = config.get('ckanext.ssm_config.aws_secret_access_key',
                                None)

        if not region_name:
            LOG.debug('region_name not found; attempting to auto-detect')
            try:
                region_name = get_instance_identity_document()['region']
            except Exception as e:
                LOG.warn("""Unable to determine AWS region due to %s;
                please specify 'ckanext.ssm_config.region_name'.""", e)
                return False

        LOG.info('Retrieving SSM parameters from region %s', region_name)
        try:
            self.client = boto3.client('ssm', region_name,
                                       aws_access_key_id=access_key,
                                       aws_secret_access_key=secret_key)
            return self.client
        except Exception as e:
            LOG.error('Failed to initialise SSM Parameter Store client: %s', e)
            return False

    def _populate_config_entries(self, config, prefix, next_token=None):
        """Retrieve all SSM parameters under 'prefix' and add them
        to the config.
        Slashes in the SSM parameter names will be converted to dots,
        and the prefix will be removed, eg a parameter named
        /CKAN/config/foo/baz with a prefix of /CKAN/config/
        will be added as config['foo.baz'].
        """
        if not prefix.endswith('/'):
            prefix += '/'

        LOG.debug('Converting all SSM parameters under %s to config entries',
                  prefix)
        try:
            if next_token:
                parameter_search = self.client.get_parameters_by_path(
                    Path=prefix,
                    Recursive=True,
                    WithDecryption=True,
                    NextToken=next_token
                )
            else:
                parameter_search = self.client.get_parameters_by_path(
                    Path=prefix,
                    Recursive=True,
                    WithDecryption=True
                )
            parameters = parameter_search['Parameters']
        except Exception as e:
            LOG.warn("Failed to retrieve parameter tree %s: %s", prefix, e)
            return

        for parameter in parameters:
            config_key = parameter['Name']\
                .replace(prefix, '').replace('/', '.')
            config_value = parameter['Value']
            LOG.debug("Populating %s from SSM", config_key)
            config[config_key] = config_value

        if 'NextToken' in parameter_search:
            self._populate_config_entries(config, prefix,
                                          parameter_search['NextToken'])

    def _replace_config_value(self, config, key):
        """Replace any SSM placeholders in a config entry.
        """
        orig_value = config[key]
        if isinstance(orig_value, six.string_types)\
                and r'${ssm:' in orig_value:
            matches = SSM_PARAMETER_SYNTAX.findall(orig_value)
            new_value = orig_value
            for match in matches:
                LOG.debug('Interpolating SSM parameter %s into entry %s',
                          match, key)
                try:
                    parameter_value = self.client.get_parameter(
                        Name=match, WithDecryption=True
                    )['Parameter']['Value']
                    new_value = new_value.replace(
                        r'${ssm:' + match + '}',
                        parameter_value
                    )
                except Exception as e:
                    LOG.warn("Unable to retrieve %s from SSM: %s", match, e)
            config[key] = new_value
