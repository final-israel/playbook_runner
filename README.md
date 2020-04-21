# Playbook Runner

A very simple library for running Ansible playbooks and retreiving their output as a dictionary.



## Usage

```python
from playbook_runner import playbook_runner as playbook_runner

ap = playbook_runner.AnsiblePlaybook('/path/to/inventory', '/path/to/ansible/playbook/directory')
ret = ap.run_playbook('playbook.yml', {'play_host_groups': 'my_group', 'param1': 'val1'})
```



## Installation

```shell
pip3 install playbook-runner
```



## Contributing

If you want to contribute to `playbook_runner` development:

1. Make a fresh fork of `playbook_runner` repository

2. Modify code as you see fit

3. Add tests to your feature

4. Go to your Github fork and create new Pull Request

   

We will thank you for every contribution :)

