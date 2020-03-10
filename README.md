Version 0.1

#ckanext-ssm-config - Amazon SSM Config CKAN Extension

#About
Queensland Government has developed this plugin to be used with data.qld.gov.au and publications.qld.gov.au.

#Features
* Config values with SSM Parameter Store placeholders, ${ssm:/path/to/value}, will be replaced at runtime.
* All SSM parameters under a prefix can be automatically converted into config entries.

#Requirements
* boto3

#Configuration
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

The 'develop' branch is automatically pushed to dev.data.qld.gov.au and dev.publications.qld.gov.au.
For deploying to higher environments, releases should be tagged and updated in the CloudFormation templates.
