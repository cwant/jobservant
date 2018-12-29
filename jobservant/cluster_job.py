from datetime import datetime
import string
import random
import base64
import re


class ClusterJob:
    DIRECTORY_RETRIES = 10
    DIRECTORY_RANDOM_CHARACTERS = 20
    DEFAULT_SUBMIT_SCRIPT_NAME = 'job_submit.sh'
    SUBMIT_JOBID_REGEX = r"Submitted batch job (\d+)"

    def __init__(self, **kwargs):
        self.cluster_account = kwargs['cluster_account']
        self.text = self.get_script_text(**kwargs)
        self.accounting_group = kwargs.get('accounting_group')
        self.time = kwargs.get('time') or None
        self.submit_script_name = self.DEFAULT_SUBMIT_SCRIPT_NAME
        self.work_directory = None
        self.submit_script_path = None
        self.jobid = None

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
                return True

        raise ValueError("Couldn't create work directory")

    def b64script(self):
        if not self.accounting_group:
            self.get_default_accounting_group()

        script = "#!/bin/sh\n"
        script += "#SBATCH --account=" + self.accounting_group + "\n"
        if self.time is not None:
            script += "#SBATCH --time=" + self.time + "\n"
        script += self.text
        return base64.b64encode(bytes(script, 'ascii')).decode('ascii')

    def get_default_accounting_group():
        # E.g., sacctmgr list account where user=cwant withassoc -p
        raise ValueError('TODO: Not Implemented')

    def construct_submit_script(self):
        if not self.work_directory:
            self.make_new_work_directory()

        script_path = self.work_directory + '/' + self.submit_script_name

        command = 'echo ' + self.b64script() + ' | base64 --decode > ' + \
            script_path
        if not self.cluster_account.simple_exec(command):
            raise ValueError('Could not create job script')
        self.submit_script_path = script_path
        return True

    def submit(self):
        if self.status()['status'] != 'not_submitted':
            raise ValueError('Job has already been submitted!')

        if not self.submit_script_path:
            self.construct_submit_script()
        command = 'cd ' + self.work_directory + ' && sbatch ' + \
            self.submit_script_path
        stdin, stdout, stderr = self.cluster_account.exec_command(command)
        out = stdout.read().decode('ascii')
        print(out)
        m = re.match(self.SUBMIT_JOBID_REGEX, out)
        if m is None:
            raise ValueError('Job did not submit right')
        self.jobid = m.groups()[0]

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

        # Fiwlds: jobid, status, submit time, start time, end time
        command = 'squeue -j ' + self.jobid + ' -o "%i,%t,%V,%S,%e"'
        stdin, stdout, stderr = self.cluster_account.exec_command(command)
        if stdout.channel.recv_exit_status() > 0:
            # Probably job finished
            stat['status'] = 'finished'
            return stat

        out = stdout.readlines()
        print(out)
        print(len(out))
        if len(out) < 2:
            # Probably job finished
            stat['status'] = 'finished'
            return stat
        fields = out[1].strip().split(',')
        job_status = fields[1]
        if job_status == 'PD':
            stat['status'] = 'waiting'
            stat['done'] = self.done_factor(fields[3], fields[2])
        elif job_status == 'R':
            stat['status'] = 'running'
            stat['done'] = self.done_factor(fields[4], fields[3])
        elif job_status == 'CG':
            stat['status'] = 'running'
            stat['done'] = 1.0
        else:
            raise ValueError('Unknown job status ' + job_status)
        return stat

    def done_factor(self, after, before):
        if 'N/A' in (before, after):
            return 0.0
        command = 'date --iso-8601=seconds'
        stdin, stdout, stderr = self.cluster_account.exec_command(command)
        out = stdout.readlines()
        now = out[0].strip()
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
