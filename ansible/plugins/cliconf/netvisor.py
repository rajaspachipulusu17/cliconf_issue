#
# (c) 2016 Red Hat Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
cliconf: netvisor
short_description: Use netvisor cliconf to run command on Pluribus netvisor platform
description:
  - This netvisor plugin provides low level abstraction apis for
    sending and receiving CLI commands from Pluribus netvisor devices.
version_added: 2.8
"""

import json
import collections
from ansible.plugins.cliconf import CliconfBase, enable_mode
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils._text import to_text
from ansible.module_utils.common._collections_compat import Mapping
from ansible.errors import AnsibleConnectionFailure


class Cliconf(CliconfBase):

    def get(self, command=None, prompt=None, answer=None, sendonly=False, output=None, check_all=False):
        if not command:
            raise ValueError('must provide value of command to execute')
        if output:
            raise ValueError("'output' value %s is not supported for get" % output)

        return self.send_command(command=command, prompt=prompt, answer=answer, sendonly=sendonly, check_all=check_all)

    def get_option_values(self):
        return {
            'format': ['text'],
            'diff_match': ['line', 'strict', 'exact', 'none'],
            'diff_replace': ['line', 'block'],
            'output': []
        }

    def get_capabilities(self):
        result = dict()
        result['rpc'] = self.get_base_rpc() + ['run_commands']
        #result = super(Cliconf, self).get_capabilities()
        #result['rpc'] += self.get_base_rpc() + ['run_commands']
#        result['rpc'] = self.get_base_rpc()
        result['network_api'] = 'cliconf'
        result['device_info'] = self.get_device_info()
        result.update(self.get_option_values())
        return json.dumps(result)

    def get_device_info(self):
        device_info = {}
        device_info['network_os'] = 'netvisor'

        return device_info


    def run_commands(self, commands=None, check_rc=False):
        if commands is None:
            raise ValueError("'commands' value is required")

        responses = list()
        for cmd in to_list(commands):
            if not isinstance(cmd, collections.Mapping):
                cmd = {'command': cmd}

            output = cmd.pop('output', None)
            if output:
                raise ValueError("'output' value %s is not supported for run_commands" % output)

            try:
                f = open("/tmp/command.txt", "a")
                f.write("cmd %s\n" % cmd)
                out = self.send_command(**cmd)
                f.write("out %s\n" % out)
                f.close()
            except AnsibleConnectionFailure as e:
                if check_rc:
                    raise
                out = getattr(e, 'err', to_text(e))

            responses.append(out)

        return responses


    @enable_mode
    def edit_config(self, candidate=None, commit=True, replace=None, comment=None):
        resp = {}
        operations = self.get_device_operations()

        results = []
        requests = []
        #self.send_command('shell')
        if commit:
            for line in to_list(candidate):
                if not isinstance(line, collections.Mapping):
                    line = {'command': line}
    
                cmd = line['command']
                if cmd != 'end' and cmd[0] != '!':
                    results.append(self.send_command(**line))
                    requests.append(cmd)
#            self.send_command('end')
        else:
            raise ValueError('check mode is not supported')

        resp['request'] = requests
        resp['response'] = results
        return resp


    def get_config(self):
        pass



    def get_diff(self, candidate=None, running=None, diff_match=None, diff_ignore_lines=None, path=None, diff_replace=None):
        pass


    def get_file(self, source=None, destination=None, proto='scp', timeout=30):
        """Fetch file over scp/sftp from remote device
        :param source: Source file path
        :param destination: Destination file path
        :param proto: Protocol to be used for file transfer,
                      supported protocol: scp and sftp
        :param timeout: Specifies the wait time to receive response from
                        remote host before triggering timeout exception
        :return: None
        """
        """Fetch file over scp/sftp from remote device"""
        ssh = self._connection.paramiko_conn._connect_uncached()
        if proto == 'scp':
            if not HAS_SCP:
                raise AnsibleError("Required library scp is not installed.  Please install it using `pip install scp`")
            with SCPClient(ssh.get_transport(), socket_timeout=timeout) as scp:
                scp.get(source, destination)
        elif proto == 'sftp':
            with ssh.open_sftp() as sftp:
                sftp.get(source, destination)


    def enable_response_logging(self):
        """Enable logging command response"""
        self.response_logging = True

    def disable_response_logging(self):
        """Disable logging command response"""
        self.response_logging = False
