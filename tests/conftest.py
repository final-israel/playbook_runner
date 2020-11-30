import pytest
import uuid
import os
import sys
import logging
import pathlib
import shutil

sys.path.append('{0}/../playbook_runner'.format(os.path.dirname(__file__)))
from playbook_runner import playbook_runner as playbook_runner


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
format = '[%(asctime)s.%(msecs)03d] [%(name)s] [%(levelname)s] ' \
         '%(message)s'

formatter = logging.Formatter(format, '%Y-%m-%d %H:%M:%S')

cons_handler = logging.StreamHandler(sys.stdout)
cons_handler.setFormatter(formatter)
LOGGER.addHandler(cons_handler)


@pytest.fixture(scope='function')
def ap(request):
    yield playbook_runner.AnsiblePlaybook(
        '{0}/../inv.ini'.format(
            os.path.dirname(__file__)
        ),
        '{0}/../playbooks_example'.format(
            os.path.dirname(__file__)
        )
    )
