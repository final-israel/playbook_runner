import os
import tempfile
import subprocess
import copy
import json
import logging
import shutil
import shlex
from string import Template
import string
import random


LOGGER = logging.getLogger('playbook_runner')


class AnsiblePlaybook(object):
    def __init__(
            self,
            ansible_playbook_inventory,
            ansible_playbook_directory,
            cleanup_output=False):
        self._ansible_playbook_inventory = ansible_playbook_inventory
        self._ansible_playbook_directory = ansible_playbook_directory

        os.environ['ANSIBLE_SSH_RETRIES'] = '15'
        os.environ['ANSIBLE_INVENTORY_UNPARSED_FAILED'] = 'true'

        self._path_str = tempfile.mkdtemp(prefix='playbook_runner_')

        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        exception_log_filename = '{0}/exception_logger.log'.format(self._path_str)
        handler = logging.FileHandler(exception_log_filename)
        handler.setFormatter(formatter)

        self._exception_logger = logging.getLogger('playbook_runner_exception_logger')
        self._exception_logger.setLevel(logging.INFO)
        self._exception_logger.addHandler(handler)

        self._hosts = set()
        self._cleanup_output = cleanup_output

        LOGGER.info('Output path: {0}'.format(self._path_str))
        LOGGER.info('CWD: {0}'.format(self._ansible_playbook_directory))

    def __del__(self):
        if self._cleanup_output:
            try:
                shutil.rmtree(self._path_str)
            except OSError as e:
                LOGGER.error(
                    'Error removing: {0}'.format(
                        self._path_str
                    )
                )

    @staticmethod
    def _get_ansible_cmd(inventory_file, playbook_file, extra_vars_dict):
        """
        Return process args list for ansible-playbook run.
        """
        ansible_command = [
            "ansible-playbook",
            "-vv",
            "--fork",
            extra_vars_dict['fork_factor'],
            "--timeout", "60",
            "-i", inventory_file,
            playbook_file,
        ]

        extra_vars = ''
        for k, v in extra_vars_dict.items():
            if type(v) == str:
                extra_vars += '{}="{}" '.format(k, v)
            else:
                extra_vars += '{}="{}" '.format(k, v)

        extra_vars = extra_vars[:-1]
        ansible_command.insert(-1, '--extra-vars')
        ansible_command.insert(-1, extra_vars)

        return ansible_command

    def _run_subprocess_ansible(cmd, skip_errors, timeout):
        cmd_for_log = [shlex.quote(s) for s in cmd]
        random_run_id = ''.join(
            random.choices(
                string.ascii_uppercase + string.digits, k=64
            )
        )

        ansible_output_path = '{0}/ansible_output_path.txt'.format(
            self._path_str
        )

        err = False
        result = None
        our_env = os.environ.copy()
        our_env["ANSIBLE_HOST_KEY_CHECKING"] = "False"
        with open(ansible_output_path, "a+") as f_ansible_output_path:
            f_ansible_output_path.write(
                '\n\nGoing to run:\n'
                '{0}\nrun_id:{1}\n\n'.format(
                    ' '.join(cmd_for_log),
                    random_run_id
                )
            )

            try:
                result = subprocess.run(
                    cmd,
                    cwd=self._ansible_playbook_directory,
                    timeout=timeout,
                    stdout=f_ansible_output_path,
                    stderr=subprocess.STDOUT,
                    env=our_env
                )
            except Exception as exc:
                self._exception_logger.error(
                    'Failed executing subprocess for '
                    'run_id: {0}\ncmd: {2}\n'.format(
                        random_run_id,
                        ' '.join(cmd_for_log)
                        )
                    )

                err = True

            if err or not skip_errors:
                if result.returncode != 0:
                    msg = 'Failed to run:\n{0}\nrun_id: {1}'.format(
                        ' '.join(cmd_for_log), random_run_id)
                    if err:
                        msg = '{0}\nCheck exception log for details'.format(msg)

                    LOGGER.error(msg)

            return err, result

    def _get_hosts_by_group(self, inventory, group):
        get_hosts_by_group_cmd = [
            "ansible",
            "--timeout",
            "60",
            "-i",
            inventory,
            '--list-hosts',
            group
        ]

        err, result = _run_subprocess_ansible(
            get_hosts_by_group_cmd,
            False,
            20
        )
        if err:
            raise RuntimeError('Failed to run list-hosts view exception log')

        hosts_in_group = []
        tmp = result.stdout.decode('utf8').split()
        i = 0
        for item in tmp:
            if item == 'hosts':
                break

            i = i + 1

        # ignore the full line "hosts (#):"
        i = i + 1
        if i >= len(tmp):
            raise RuntimeError(
                'No hosts were found for group: {0}'.format(group)
            )

        for k in range(i + 1, len(tmp)):
            hosts_in_group.append(tmp[k])

        return hosts_in_group

    def _generate_parent_play(self, dir_path, play_filename):
        playbook_path = os.path.join(dir_path, play_filename)
        tmplt_path = os.path.join(os.path.dirname(__file__), 'parent_play.tmplt')
        parent_path = '{0}/{1}.json'.format(self._path_str, play_filename + '.parent')

        with open(tmplt_path, "r") as tmplt_file:
            tmplt = Template(tmplt_file.read())

        with open(parent_path, 'w') as parent_file:
            parent_file.write(tmplt.substitute({"PLAYBOOK_PATH": playbook_path}))

        return parent_path

    def run_playbook(self, play_filename, extra_vars_dict=None):
        if not extra_vars_dict:
            extra_vars_dict = {}

        local_extra_vars = copy.deepcopy(extra_vars_dict)
        local_extra_vars['playbooks_output_path'] = self._path_str
        if 'skip_errors' not in local_extra_vars:
            local_extra_vars['skip_errors'] = False
        if 'gather_facts_for_pb' not in local_extra_vars:
            local_extra_vars['gather_facts_for_pb'] = False
        if 'play_host_groups' not in local_extra_vars:
            local_extra_vars['play_host_groups'] = 'localhost'
        if 'fork_factor' not in local_extra_vars:
            local_extra_vars['fork_factor'] = 50
        if 'max_timeout' not in local_extra_vars:
            local_extra_vars['max_timeout'] = 120

        if not self._hosts:
            local_hosts = ['localhost', '127.0.0.1']
            hosts = self._get_hosts_by_group(
                self._ansible_playbook_inventory,
                'all'
            )

            group = local_extra_vars['play_host_groups']
            if not hosts and group not in local_hosts:
                raise RuntimeError(
                    'Failed to list hosts. Will use localhost only'
                )

            hosts.extend(local_hosts)
            self._hosts.update(hosts)

        path = self._generate_parent_play(self._ansible_playbook_directory, play_filename)
        cmd = self._get_ansible_cmd(
            self._ansible_playbook_inventory,
            path,
            extra_vars_dict=local_extra_vars)

        for host in self._hosts:
            file_path = '{0}/{1}.json'.format(self._path_str, host)
            if not os.path.isfile(file_path):
                with open(file_path, 'w') as f:
                    f.write('[')

        err, result = _run_subprocess_ansible(
            cmd,
            local_extra_vars['skip_errors'],
            local_extra_vars['max_timeout']
        )
        if err:
            raise RuntimeError('Failed to run playbook view exception log')

        return result.returncode

    def get_output(self):
        last_output = {}
        for host in self._hosts:
            data = []
            file_path = '{0}/{1}.json'.format(self._path_str, host)
            with open(file_path) as f:
                lines = f.readlines()
                data = lines

            # format file into a correct json format
            with open(file_path, "w") as f:
                last_line = data[-1]
                last_line = last_line.strip()[:-1]
                data[-1] = last_line
                f.writelines(data)
                f.write(']')

            with open(file_path) as f:
                try:
                    last_output[host] = json.load(f)
                except Exception:
                    pass

            os.remove(file_path)

            # Only if the playbook has written something
            if len(data) <= 1:
                continue

        host_output_dict = {}
        for k, v in last_output.items():
            host_output_dict[k] = []
            for item in v:
                host_output_dict[k].append(item[0])

        return host_output_dict
