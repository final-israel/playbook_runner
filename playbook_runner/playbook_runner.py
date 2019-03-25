import os
import tempfile
import subprocess
import copy
import json
import logging

LOGGER = logging.getLogger()


class AnsiblePlaybook(object):
    def __init__(self, ansible_playbook_inventory, ansible_playbook_directory):
        self._ansible_playbook_inventory = ansible_playbook_inventory
        self._ansible_playbook_directory = ansible_playbook_directory

        os.environ['ANSIBLE_SSH_RETRIES'] = '15'
        os.environ['ANSIBLE_INVENTORY_UNPARSED_FAILED'] = 'true'

    @staticmethod
    def _get_ansible_cmd(inventory_file, playbook_file,
                        extra_vars_dict=None):
        """
        Return process args list for ansible-playbook run.
        """
        ansible_command = [
            "ansible-playbook",
            "-vv",
            "--fork",
            "50",
            "--timeout", "60",
            "-i", inventory_file,
            playbook_file,
        ]
        if extra_vars_dict:
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

    def _get_hosts_by_group(self, inventory, group, some_playbook):
        get_hosts_by_group_cmd = [
            "ansible-playbook",
            "--timeout",
            "60",
            '--list-hosts',
            "-i",
            inventory,
            some_playbook,
            '-e',
            '{0}={1}'.format('play_host_groups', group)
        ]

        result = subprocess.run(
            get_hosts_by_group_cmd,
            cwd=self._ansible_playbook_directory,
            timeout=60,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE
        )

        if result.returncode != 0:
            raise RuntimeError(
                'Failed to run list-hosts. stdout: {0}, stderr: {1}'.format(
                    result.stdout,
                    result.stderr
                )
            )

        hosts_in_group = []
        tmp = result.stdout.decode('utf8').split()
        i = 0
        for item in tmp:
            if item == 'hosts':
                break

            i = i + 1

        if i == len(tmp):
            raise RuntimeError(
                'No hosts were found for group: {0}'.format(group)
            )

        for k in range(i + 1, len(tmp)):
            hosts_in_group.append(tmp[k])

        return hosts_in_group

    def run_playbook(self, play_filename, extra_vars_dict={}):
        if not extra_vars_dict:
            extra_vars_dict = {'play_host_groups': 'localhost'}

        with tempfile.TemporaryDirectory() as tmp_dir_name:
            path_str = '{0}/'.format(tmp_dir_name)
            local_extra_vars = copy.deepcopy(extra_vars_dict)
            local_extra_vars['output_path'] = path_str
            if 'skip_errors' not in local_extra_vars:
                local_extra_vars['skip_errors'] = False
            if 'gather_facts_for_pb' not in local_extra_vars:
                local_extra_vars['gather_facts_for_pb'] = False

            cmd = self._get_ansible_cmd(
                self._ansible_playbook_inventory,
                '{0}/{1}'.format(
                    self._ansible_playbook_directory, play_filename),
                extra_vars_dict=local_extra_vars)

            hosts = self._get_hosts_by_group(
                self._ansible_playbook_inventory,
                extra_vars_dict['play_host_groups'],
                '{0}/{1}'.format(
                    self._ansible_playbook_directory,
                    play_filename
                ),
            )

            for host in hosts:
                file_path = '{0}/{1}.json'.format(path_str, host)
                with open(file_path, "w") as f:
                    f.write('[')

            LOGGER.info(
                'Command is about to be run:\n{0}'.format(' '.join(cmd))
            )
            LOGGER.info('CWD: {0}'.format(self._ansible_playbook_directory))

            result = subprocess.run(
                cmd,
                cwd=self._ansible_playbook_directory,
                timeout=120,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE
            )

            last_output = {}
            for host in hosts:
                data = None
                file_path = '{0}/{1}.json'.format(path_str, host)
                with open(file_path) as f:
                    lines = f.readlines()
                    data = lines

                # Only if the playbook has written something
                if len(data) <= 1:
                    continue

                # format file into a correct json format
                with open(file_path, "w+") as f:
                    last_line = data[len(data) - 1]
                    last_line = last_line[:-3]
                    data[len(data) - 1] = last_line
                    f.writelines(data)
                    f.write(']')

                with open(file_path) as f:
                    last_output[host] = json.load(f)

        host_output_dict = {}
        for k, v in last_output.items():
            host_output_dict[k] = []
            for item in v:
                host_output_dict[k].append(item[0])

        LOGGER.info('\nSTDOUT:\n{0}'.format(result.stdout.decode('utf-8')))
        LOGGER.info('\nSTDERR:\n{0}'.format(result.stderr.decode('utf-8')))

        if 'skip_errors' not in extra_vars_dict or not extra_vars_dict[
            'skip_errors']:
            assert 0 == result.returncode

        return host_output_dict
