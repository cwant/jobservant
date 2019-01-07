from datetime import datetime
import string
import random
import base64
import re
from .has_a_logger import HasALogger


class ClusterJob(HasALogger):
    DIRECTORY_RETRIES = 10
    DIRECTORY_RANDOM_CHARACTERS = 20
    DEFAULT_SUBMIT_SCRIPT_NAME = 'job_submit.sh'
    SUBMIT_JOBID_REGEX = r"Submitted batch job (\d+)"
    ALLOWED_JOB_PARAMS = ['account', 'time', 'mem', 'pmem']
    SEFF_FIELD_MAP = {
        'State': 'state',
        'CPU Utilized': 'cpu_utilized',
        'CPU Efficiency': 'cpu_efficiency',
        'Memory Utilized': 'memory_utilized',
        'Memory Efficiency': 'memory_efficiency',
        'Job Wall-clock time': 'walltime'
    }
    SEFF_EXIT_CODE_REGEX = r"COMPLETED \(exit code (\d+)\)"

    def __init__(self, **kwargs):
        self.cluster_account = kwargs['cluster_account']
        self.text = self.get_script_text(**kwargs)

        self.job_params = {}
        for key in self.ALLOWED_JOB_PARAMS:
            self.job_params[key] = kwargs.get(key)

        self.submit_script_name = self.DEFAULT_SUBMIT_SCRIPT_NAME
        self.work_directory = None
        self.submit_script_path = None
        self.jobid = None
        self.init_logging(log_level=kwargs.get('log_level',
                                               self.cluster_account.log_level))

    def get_script_text(self, **kwargs):
        if kwargs.get('text') is not None:
            return kwargs.get('text')

        if kwargs.get('script') is not None:
            f = open(kwargs['script'], "r")
            text = f.read()
            f.close
            return text
        raise ValueError('No script text provided')

    def make_new_work_directory(self):
        self.cluster_account.ensure_workspace_exists()

        self.log('info', 'Constructing work directory ...')

        tries = self.DIRECTORY_RETRIES
        while (tries > 0):
            tries -= 1

            directory = self.cluster_account.workspace + '/cluster_job_' + \
                ''.join(random.choices(string.ascii_letters + string.digits,
                                       k=self.DIRECTORY_RANDOM_CHARACTERS))
            if (not self.cluster_account.does_directory_exist(directory)):
                if (not self.cluster_account.mkdir(directory)):
                    raise ValueError("Couldn't create work directory " +
                                     directory)
                self.work_directory = directory
                self.log('info', 'Work directory %s created' % (directory))
                return True

        raise ValueError("Couldn't create work directory")

    def construct_submit_file_contents(self):
        if not self.job_params.get('account'):
            self.get_default_accounting_group()

        script = "#!/bin/sh\n"

        for key in self.job_params:
            value = self.job_params.get(key)
            if value is not None:
                script += "#SBATCH --%s=%s\n" % (key, value)

        script += self.text
        return script

    def b64file(self, contents):
        return base64.b64encode(bytes(contents, 'ascii')).decode('ascii')

    def get_default_accounting_group():
        # E.g., sacctmgr list account where user=cwant withassoc -p
        raise ValueError('TODO: Not Implemented')

    def construct_submit_script(self):
        contents = self.construct_submit_file_contents()
        self.submit_script_path = \
            self.create_remote_file(self.submit_script_name, contents)
        return True

    def create_remote_file(self, filename, contents):
        if not self.work_directory:
            self.make_new_work_directory()
        self.log('info', 'Creating remote file %s ...' % filename)
        file_path = self.work_directory + '/' + filename
        command = 'echo %s | base64 --decode > %s' % (self.b64file(contents),
                                                      file_path)
        if not self.cluster_account.simple_exec(command):
            raise ValueError('Could not create file')
        self.log('info', 'File %s created' % file_path)
        return file_path

    def submit(self):
        if self.status()['status'] != 'not_submitted':
            raise ValueError('Job has already been submitted!')

        if not self.submit_script_path:
            self.construct_submit_script()

        self.log('info', 'Submitting job ...')
        command = 'cd ' + self.work_directory + ' && sbatch ' + \
            self.submit_script_path
        stdin, stdout, stderr = self.cluster_account.exec_command(command)
        out = stdout.read().decode('ascii')
        m = re.match(self.SUBMIT_JOBID_REGEX, out)
        if m is None:
            raise ValueError('Job did not submit right')
        self.jobid = m.groups()[0]

        self.log('info', out)

        return True

    def clean_work_directory(self):
        if not self.work_directory:
            raise ValueError('No work directory to clean')
        command = 'rm -rf ' + self.work_directory
        return self.cluster_account.simple_exec(command)

    def status(self):
        if self.jobid is None:
            return {'status': 'not_submitted'}
        stat = {'jobid': self.jobid}
        stat['status'] = 'submitted'

        queue_status = self.queue_status_hash()
        if queue_status == {}:
            stat['status'] = 'finished'
            return stat

        job_status = queue_status['ST']
        if job_status == 'PD':
            stat['status'] = 'waiting'
            stat['done'] = self.done_factor(queue_status['START_TIME'],
                                            queue_status['SUBMIT_TIME'])
        elif job_status == 'R':
            stat['status'] = 'running'
            stat['done'] = self.done_factor(queue_status['END_TIME'],
                                            queue_status['START_TIME'])
        elif job_status == 'CG':
            stat['status'] = 'running'
            stat['done'] = 1.0
        else:
            raise ValueError('Unknown job status ' + job_status)
        return stat

    def queue_status_hash(self):
        command = 'squeue -j ' + self.jobid + ' -o "%all"'
        stdin, stdout, stderr = self.cluster_account.exec_command(command)
        if stdout.channel.recv_exit_status() > 0:
            # Probably job finished
            return {}

        out = stdout.readlines()
        self.log('debug', 'squeue output:\n' + ''.join(out))
        if len(out) < 2:
            # Probably job finished
            return {}

        header = out[0].strip().split('|')
        fields = out[1].strip().split('|')
        output_hash = {}
        for i in range(len(header)):
            if len(header[i]) > 0:
                output_hash[header[i]] = fields[i]

        return output_hash

    def efficiency_hash(self):
        # TODO: consider using sacct output to create more flexible output
        command = 'seff -j ' + self.jobid
        stdin, stdout, stderr = self.cluster_account.exec_command(command)
        if stdout.channel.recv_exit_status() > 0:
            # Probably job finished
            return {}

        out = stdout.readlines()
        self.log('debug', 'seff output:\n' + ''.join(out))
        if len(out) < 2:
            # Probably job finished
            return {}

        self.log('debug', out)

        output_hash = {}
        for row in out:
            (heading, data) = row.strip().split(': ', 1)
            if heading in self.SEFF_FIELD_MAP:
                new_heading = self.SEFF_FIELD_MAP[heading]
                output_hash[new_heading] = data

                if new_heading == 'state':
                    m = re.match(self.SEFF_EXIT_CODE_REGEX, data)
                    if m is not None:
                        output_hash['exit_code'] = m.groups()[0]

                if new_heading == 'state':
                    m = re.match(self.SEFF_EXIT_CODE_REGEX, data)
                    if m is not None:
                        output_hash['exit_code'] = m.groups()[0]

        return output_hash

    def done_factor(self, after, before):
        if 'N/A' in (before, after):
            return 0.0
        command = 'date --iso-8601=seconds'
        stdin, stdout, stderr = self.cluster_account.exec_command(command)
        out = stdout.readlines()
        # Ensure timezone and carriage return are stripped off
        now = out[0][:19]
        before_f = datetime.fromisoformat(before).timestamp()
        after_f = datetime.fromisoformat(after).timestamp()
        now_f = datetime.fromisoformat(now).timestamp()
        denom = after_f - before_f
        if denom < 0.01:
            return 0.0
        return (now_f - before_f) / denom

    def output(self):
        stat = self.status()
        if stat['status'] != 'finished':
            raise ValueError('Job is in state ' + stat['status'])

        output_file = self.work_directory + '/slurm-' + self.jobid + '.out'
        command = 'cat ' + output_file
        stdin, stdout, stderr = self.cluster_account.exec_command(command)
        return stdout.read().decode('ascii')
