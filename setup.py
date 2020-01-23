from setuptools import setup, find_packages

version='@BUILD-LABEL@'

setup(
    name='ckanext-ssm-config',
    version=version,
    description='Interpolates Amazon SSM Parameter Store values into CKAN config',
    long_description='',
    classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='',
    author='Digital Applications',
    author_email='qol.development@smartservice.qld.gov.au',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['ckanext', 'ckanext.ssm'],
    include_package_data=True,
    zip_safe=False,
    install_requires=['boto3', 'six'],
    entry_points=\
    """
    [ckan.plugins]
    ssm_config=ckanext.ssm.plugin:SSMConfigPlugin
    """,
)
