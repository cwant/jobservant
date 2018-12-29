import paramiko
import getpass
from .cluster_job import ClusterJob


class ClusterAccount:
    def __init__(self, server, **kwargs):
        self.server = server
        self.ssh = None

        if kwargs.get('username') is not None:
            self.username = kwargs['username']
        else:
            self.username = getpass.getuser()

        if kwargs.get('workspace') is not None:
            self.workspace = kwargs['workspace']
        else:
            self.workspace = '/scratch/' + self.username

        self.debug = False
        if kwargs.get('debug') is not None:
            self.debug = kwargs['debug']
        self.workspace_verified = False

    def connect(self):
        if (self.ssh is None):
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.connect(self.server, username=self.username)

    def exec_command(self, command):
        self.connect()
        if self.debug:
            print(command)
        return self.ssh.exec_command(command)

    # TODO: YUCK?
    def simple_exec(self, command):
        stdin, stdout, stderr = self.exec_command(command)
        code = stdout.channel.recv_exit_status()
        if code == 0:
            return True
        return False

    def does_directory_exist(self, directory):
        command = 'test -d ' + directory
        return self.simple_exec(command)

    def ensure_workspace_exists(self):
        if self.workspace_verified:
            return True

        if self.does_directory_exist(self.workspace):
            self.workspace_verified = True
            return True
        raise ValueError('Workspace directory ' + self.workspace +
                         ' does not exist on cluster ' + self.server)

    def mkdir(self, directory):
        command = 'mkdir -p ' + directory
        return self.simple_exec(command)

    def submit_job(self, **kwargs):
        self.ensure_workspace_exists()
        job = ClusterJob(cluster_account=self, **kwargs)
        job.submit()
        return job
