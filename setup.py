import setuptools

description = 'A module that is capable of running ansible playbooks'

setuptools.setup(
    name='playbook_runner',
    version="0.0.1",
    author="Pavel Rogovoy",
    author_email='pavelr@final.israel',
    description=description,
    long_description=open('README').read(),
    package_dir={'playbook_runner': 'playbook_runner'},
    packages=['playbook_runner',],
)
