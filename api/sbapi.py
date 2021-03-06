# Copyright (c) 2017 by Telcoware
# All Rights Reserved.
# SONA Monitoring Solutions.

from subprocess import Popen, PIPE

from config import CONF
from sona_log import LOG


class SshCommand:
    ssh_options = '-o StrictHostKeyChecking=no ' \
              '-o ConnectTimeout=' + str(CONF.ssh_conn()['ssh_req_timeout'])

    @classmethod
    def ssh_exec(cls, username, node, command):
        cmd = 'ssh %s %s@%s %s' % (cls.ssh_options, username, node, command)

        try:
            result = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            output, error = result.communicate()

            if result.returncode != 0:
                LOG.error("\'%s\' SSH_Cmd Fail, cause => %s", node, error)
                return
            else:
                # LOG.info("ssh command execute successful \n%s", output)
                return output
        except:
            LOG.exception()

    @classmethod
    def onos_ssh_exec(cls, node, command):

        local_ssh_options = cls.ssh_options + " -p 8101"

        cmd = 'ssh %s %s %s' % (local_ssh_options, node, command)

        try:
            result = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
            output, error = result.communicate()

            if result.returncode != 0:
                LOG.error("ONOS(%s) SSH_Cmd Fail, cause => %s", node, error)
                return
            else:
                # LOG.info("ONOS ssh command execute successful \n%s", output)
                return output
        except:
            LOG.exception()

