# encoding: utf-8
""" SSM Config CKAN extension.
This provides Amazon SSM Parameter Store interpolations into config values.
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types_boto3_ssm import SSMClient
    from types_boto3_ssm.type_defs import GetParametersByPathResultTypeDef
else:
    SSMClient = object
    GetParametersByPathResultTypeDef = object

import re
import requests
import six

from logging import getLogger

import boto3

from ckan import plugins
from ckan.common import CKANConfig

LOG = getLogger(__name__)
SSM_PARAMETER_SYNTAX = re.compile(r'[${][{]ssm:(/[-a-zA-Z0-9_./]+)(?::([^}]*))?[}][}]?')


def get_instance_identity_document():
    token = requests.put(
        'http://169.254.169.254/latest/api/token',
        headers={'X-aws-ec2-metadata-token-ttl-seconds': '60'}
    ).text
    return requests.get(
        'http://169.254.169.254/latest/dynamic/instance-identity/document',
        headers={'X-aws-ec2-metadata-token': token}
    ).json()


class SSMConfigPlugin(plugins.SingletonPlugin):
    """Interpolate SSM Parameter Store values into config.
    """
    plugins.implements(plugins.IConfigurer, inherit=True)

    client: 'SSMClient|None' = None

    # IConfigurer

    def update_config(self, config: CKANConfig):
        """Replace any values containing SSM references
        """
        if not self._make_client(config):
            LOG.warning("""Failed to configure SSM client.
            Parameters will NOT be interpolated from SSM!""")
            return config
        prefix = config.get('ckanext.ssm_config.prefix', None)
        if prefix:
            self._populate_config_entries(config, prefix)

        for key in config:
            self._replace_config_value(config, key)
        return config

    def _make_client(self, config: CKANConfig) -> 'SSMClient|bool':
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
            except Exception:
                LOG.warning("""Unable to determine AWS region,
                 please specify 'ckanext.ssm_config.region_name'.""", exc_info=True)
                return False

        LOG.info('Retrieving SSM parameters from region %s', region_name)
        try:
            self.client = boto3.client('ssm', region_name,
                                       aws_access_key_id=access_key,
                                       aws_secret_access_key=secret_key)
            return self.client
        except Exception:
            LOG.exception('Failed to initialise SSM Parameter Store client')
            return False

    def _populate_config_entries(self, config: CKANConfig, prefix: str, next_token: 'str|None' = None):
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
        if self.client:
            try:
                if next_token:
                    parameter_search: GetParametersByPathResultTypeDef = self.client.get_parameters_by_path(
                        Path=prefix,
                        Recursive=True,
                        WithDecryption=True,
                        NextToken=next_token
                    )
                else:
                    parameter_search: GetParametersByPathResultTypeDef = self.client.get_parameters_by_path(
                        Path=prefix,
                        Recursive=True,
                        WithDecryption=True
                    )
                parameters = parameter_search['Parameters']
            except Exception:
                LOG.warning("Failed to retrieve parameter tree %s", prefix, exc_info=True)
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

    def _replace_config_value(self, config: CKANConfig, key: str):
        """Replace any SSM placeholders in a config entry.
        """
        orig_value = config[key]
        if self.client:
            if isinstance(orig_value, six.string_types)\
                    and r'{ssm:' in orig_value:
                matches = SSM_PARAMETER_SYNTAX.findall(orig_value)
                new_value = orig_value
                for match in matches:
                    parameter_name = match[0]
                    default_value = match[1]
                    LOG.debug('Interpolating SSM parameter %s into entry %s',
                              parameter_name, key)
                    try:
                        parameter_value = self.client.get_parameter(
                            Name=parameter_name, WithDecryption=True
                        )['Parameter']['Value']
                    except Exception:
                        LOG.warning("Unable to retrieve %s from SSM, defaulting to [%s]",
                                    parameter_name, default_value, exc_info=True)
                        parameter_value: str = default_value
                    new_value = re.sub(
                        r'[${][{]ssm:' + parameter_name + '(:[^}]*)?[}][}]?',
                        parameter_value,
                        new_value
                    )
                config[key] = new_value
