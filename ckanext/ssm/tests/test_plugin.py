# encoding: utf-8

import pytest
from unittest.mock import MagicMock

from ckanext.ssm.plugin import SSMConfigPlugin


class TestPlugin(object):

    def setup_method(self):
        # configure a fake SSM Parameter Store to talk to
        self.plugin = SSMConfigPlugin()

    # Config

    def test_gracefully_failed_client_creation(self):
        config = {'foo': 'baz'}
        self.plugin._make_client = lambda c: False

        self.plugin.update_config(config)

        assert config == {'foo': 'baz'}

    # Parameter interpolation

    @pytest.mark.parametrize('original_value,expected_value', [
        ('${ssm:/test}', 'foo'),
        ('literal-${ssm:/test}', 'literal-foo'),
        ('{{ssm:/test}}', 'foo'),
        ('literal-{{ssm:/test}}', 'literal-foo'),
        ('literal-{{ssm:/test}}-literal2-${ssm:/test}', 'literal-foo-literal2-foo'),
    ])
    def test_insert_parameter(self, original_value, expected_value):
        """ test succession insertions of parameter
        """
        config = {'test_parameter': original_value}
        client = MagicMock()
        client.get_parameter.return_value = {'Parameter': {'Value': 'foo'}}

        self.plugin._replace_config_value(client, config, 'test_parameter')

        assert config.get('test_parameter') == expected_value

    @pytest.mark.parametrize('original_value,expected_value', [
        ('${ssm:/test}', ''),
        ('literal-${ssm:/test}', 'literal-'),
        ('${ssm:/test:}', ''),
        ('literal-${ssm:/test:}', 'literal-'),
        ('{{ssm:/test}}', ''),
        ('literal-{{ssm:/test}}', 'literal-'),
        ('{{ssm:/test:foo}}', 'foo'),
        ('literal-{{ssm:/test:foo}}', 'literal-foo'),
        ('literal-{{ssm:/test:foo}}-literal2-${ssm:/test2:baz}', 'literal-foo-literal2-baz'),
    ])
    def test_insert_missing_parameter(self, original_value, expected_value):
        """ test insertions when parameter was not successfully retrieved
        """
        config = {'test_parameter': original_value}
        client = MagicMock()
        client.get_parameter.side_effect = Exception("unit test")

        self.plugin._replace_config_value(client, config, 'test_parameter')

        assert config.get('test_parameter') == expected_value

    def test_insert_parameters(self):
        """ Test that all parameters under a specified prefix are retrieved
        """
        config = {'foo': 'baz'}
        client = MagicMock()
        client.get_parameters_by_path.return_value = {
            'Parameters': [
                {'Name': '/test/unit/key1', 'Value': 'meh'},
                {'Name': '/test/unit/key2', 'Value': 'quux'},
            ]
        }

        self.plugin._populate_config_entries(client, config, '/test/')
        assert config == {
            'foo': 'baz',
            'unit.key1': 'meh',
            'unit.key2': 'quux'
        }
