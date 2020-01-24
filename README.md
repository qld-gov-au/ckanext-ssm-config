Version 0.1

#ckanext-ssm-config - Amazon SSM Config CKAN Extension

#About
Queensland Government has developed this plugin to be used with data.qld.gov.au and publications.qld.gov.au.

#Features
* Config values with SSM Parameter Store placeholders, ${ssm:/path/to/value}, will be replaced at runtime.

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
```

If the region is not configured, the extension will attempt to query AWS metadata to determine the
region of the machine where CKAN is running. If this lookup fails, the extension will do nothing.

# Development

The 'develop' branch is automatically pushed to dev.data.qld.gov.au and dev.publications.qld.gov.au.
For deploying to higher environments, releases should be tagged and updated in the CloudFormation templates.
