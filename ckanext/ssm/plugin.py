# encoding: utf-8
""" SSM Config CKAN extension.
This provides Amazon SSM Parameter Store interpolations into config values.
"""
from logging import getLogger

from ckan.plugins import implements, SingletonPlugin, IConfigurer

LOG = getLogger(__name__)

class SSMConfigPlugin(SingletonPlugin):
    """Interpolate SSM Parameter Store values into config.
    """
    implements(IConfigurer, inherit=True)

    def update_config(self, ckan_config):
        """Replace any values containing SSM references
        """
        LOG.info("TODO interpolate SSM config values")
        return ckan_config
