Version 0.1

#ckanext-ssm-config - Amazon SSM Config CKAN Extension

#About
Queensland Government has developed this plugin to be used with data.qld.gov.au and publications.qld.gov.au.

#Features
* Config values with SSM Parameter Store placeholders, ${ssm:/path/to/value}, will be replaced at runtime.

#Requirements
* None

#Configuration
```
ckan.plugins = ssm-config
```

# Development

The 'develop' branch is automatically pushed to dev.data.qld.gov.au and dev.publications.qld.gov.au.
For deploying to higher environments, releases should be tagged and updated in the CloudFormation templates.
