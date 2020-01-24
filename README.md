Version 0.1

#ckanext-ssm-config - Amazon SSM Config CKAN Extension

#About
Queensland Government has developed this plugin to be used with data.qld.gov.au and publications.qld.gov.au.

#Features
* Config values with SSM Parameter Store placeholders, ${ssm:/path/to/value}, will be replaced at runtime.
* All SSM parameters under a prefix can be automatically converted into config entries.

#Requirements
* boto
* boto3

#Configuration
```
ckan.plugins = ssm_config
```

Optional:

```
ckanext.ssm_config.region_name = <region>
ckanext.ssm_config.prefix = /path/to/config/
```

If the region is not configured, the extension will attempt to query AWS metadata to determine the
region of the machine where CKAN is running. If this lookup fails, the extension will do nothing.

If a prefix is configured, the extension will attempt to load all parameters under this prefix as
config entries, with slashes being converted to dots.

For example, if the prefix is set to /CKAN/ssm/, and the SSM Parameter Store contains the key
``/CKAN/ssm/sqlalchemy/url``, then the extension will populate ``config['sqlalchemy.url']``
with the SSM value.

# Development

The 'develop' branch is automatically pushed to dev.data.qld.gov.au and dev.publications.qld.gov.au.
For deploying to higher environments, releases should be tagged and updated in the CloudFormation templates.
