import setuptools
from playbook_runner import version

description = 'A module that is capable of running ansible playbooks'

setuptools.setup(
    name='playbook_runner',
    version=version.version,
    author="Pavel Rogovoy",
    author_email='pavelr@final.israel',
    url="https://github.com/final-israel/playbook_runner",
    description=description,
    include_package_data=True,
    long_description=description,
    package_dir={'playbook_runner': 'playbook_runner'},
    packages=['playbook_runner',],
)
