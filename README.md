[![Tests](https://github.com/qld-gov-au/ckanext-ssm-config/actions/workflows/test.yml/badge.svg)](https://github.com/qld-gov-au/ckanext-ssm-config/actions/workflows/test.yml)
================
ckanext-ssm-config - Amazon SSM Config CKAN Extension
================

# About

This plugin enables CKAN config options to be retrieved at runtime from AWS Parameter Store.

This is particularly useful for automatically managed environments, so that dynamic or secret values such as the Beaker session key, XLoader job tokens, or Google reCAPTCHA private keys, can be stored securely outside the configuration management system.

Unfortunately the current CKAN architecture does not allow for database passwords to be handled by this plugin, as the password is read from the config before this plugin has the chance to inject it.

Queensland Government has developed this plugin to be used with data.qld.gov.au and publications.qld.gov.au.

# Features
* Config values with SSM Parameter Store placeholders, `${ssm:/path/to/value}` or `{{ssm:/path/to/value}}`, will be replaced at runtime.
* Values that cannot be retrieved from the Parameter Store will result in blanks, or a fallback value can be supplied, eg `{{ssm:/path/to/value:default_value}}`
* All SSM parameters under a prefix can be automatically converted into config entries.

# Requirements
* boto3

# Configuration
```
ckan.plugins = ssm_config
```

IAM permissions similar to the following are needed:

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:GetParametersByPath"
            ],
            "Resource": [
                "arn:aws:ssm:*:*:parameter/CKAN/config/",
                "arn:aws:ssm:*:*:parameter/CKAN/config/*",
            ],
            "Effect": "Allow"
        }
    ]
}
```

Optional:

```
ckanext.ssm_config.region_name = <region>
ckanext.ssm_config.prefix = /CKAN/config/
ckanext.ssm_config.aws_access_key_id = abcde
ckanext.ssm_config.aws_secret_access_key = ABCDE
```

If ``region_name`` is not configured, the extension will attempt to query AWS metadata to determine
the region of the machine where CKAN is running.

If ``prefix`` is configured, the extension will attempt to load all parameters under this prefix as
config entries, with slashes being converted to dots. For example, if the prefix is set to
`` /CKAN/config/``, and the SSM Parameter Store contains the key ``/CKAN/config/sqlalchemy/url``, then
the extension will populate ``config['sqlalchemy.url']`` with the SSM value.

If ``aws_access_key_id`` and ``aws_secret_access_key`` are not configured, the extension will
proceed on the assumption that permissions are being managed through an EC2 instance role.

# Development

To install this plugin for development:

1. Activate your Python virtual environment, eg `. /usr/lib/ckan/default/bin/activate`

1. Install the plugin and its dependencies:

    git clone https://github.com/qld-gov-au/ckanext-ssm-config.git
    cd ckanext-ssm-config
    pip install -e .
    pip install -r requirements.txt -r dev-requirements.txt

