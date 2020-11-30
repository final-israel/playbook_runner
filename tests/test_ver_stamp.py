import pytest
import sys
import os
import copy

sys.path.append('{0}/../playbook_runner'.format(os.path.dirname(__file__)))
from playbook_runner import playbook_runner as playbook_runner


def run_shell_command(host, cmd, ap):
    return ap.run_playbook(
        'run_shell_command.yml',
        {'play_host_groups': host,
         'shell_command': cmd
         }
    )


def test_basic_stamp(ap):
    ret = run_shell_command('172.17.0.2', 'hostname', ap)
    assert ret == 0

    ret = run_shell_command('172.17.0.2', 'ls', ap)
    assert ret == 0

    ret = ap.get_output()
    assert ret['172.17.0.2'][0]['stdout'] == 'openssh-server'
