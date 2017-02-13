"""Setup scripts."""
from distutils.core import setup


setup(
    name='chatty',
    version='0.0.1',
    package_dir={'chatty': 'chatty'},
    packages=['chatty', 'chatty.server', 'chatty.api']
)
