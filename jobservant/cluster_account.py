import paramiko
import getpass
from .cluster_job import ClusterJob
from .has_a_logger import HasALogger


class ClusterAccount(HasALogger):
    def __init__(self, server, **kwargs):
        self.server = server
        self.ssh = None

        self.username = kwargs.get('username', getpass.getuser())
        self.workspace = kwargs.get('workspace',
                                    '/scratch/' + self.username)

        self.init_logging(**kwargs)

        self.workspace_verified = False

    def connect(self):
        if (self.ssh is None):
            self.log('info', 'Connecting to %s@%s' %
                     (self.username, self.server))
            self.ssh = paramiko.SSHClient()
            self.ssh.load_system_host_keys()
            self.ssh.connect(self.server, username=self.username)

    def exec_command(self, command):
        self.connect()
        self.log('debug', command)
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

    def create_job(self, **kwargs):
        self.ensure_workspace_exists()
        return ClusterJob(cluster_account=self, **kwargs)

    def submit_job(self, **kwargs):
        job = self.create_job(**kwargs)
        job.submit()
        return job
