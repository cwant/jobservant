import time
import ipywidgets
from IPython.lib import backgroundjobs
from IPython.display import display


class JobProgress:

    def __init__(self, cluster_job, **kwargs):
        self.cluster_job = cluster_job
        self.suppress_output = kwargs.get('suppress_output', False)

        # Widgets
        self.waiting_progress = None
        self.running_progress = None
        self.status_field = None
        self.output_field = None

        self.output = None
        self.initialized = False
        self.iteration = None
        self.finished = False
        self.sleep_seconds = 20.0

    def init(self):
        if self.initialized:
            return
        self.iteration = 0
        self.create_status_field()
        self.create_waiting_progress()
        self.create_running_progress()
        if not self.suppress_output:
            self.create_output_field()

        self.initialized = True

    def run(self):
        self.init()
        while(not self.finished):
            self.update()
            self.wait()

    def run_in_background(self):
        jobs = backgroundjobs.BackgroundJobManager()
        jobs.new(self.run)

    def create_waiting_progress(self):
        self.waiting_progress = ipywidgets.FloatProgress(
            value=0.0,
            min=0.0,
            max=1.0,
            description='Waiting:',
            bar_style='info',
            orientation='horizontal'
        )
        display(self.waiting_progress)

    def create_running_progress(self):
        self.running_progress = ipywidgets.FloatProgress(
            value=0.0,
            min=0.0,
            max=1.0,
            description='Running:',
            bar_style='info',
            orientation='horizontal'
        )
        display(self.running_progress)

    def create_output_field(self):
        self.output_field = ipywidgets.HTML(
            value='',
            description='Output:',
        )
        display(self.output_field)

    def create_status_field(self):
        self.status_field = ipywidgets.HTML(
            value='Initializing ...',
            description='Status:',
        )
        display(self.status_field)

    def update(self):
        self.iteration += 1
        self.status_field.value = \
            'Checking ... (Iteration %d)' % (self.iteration)
        status = self.cluster_job.status()
        if status['status'] == 'finished':
            self.finished = True
            self.waiting_done()
            self.running_done()
            if not self.suppress_output:
                html = '<pre>' + self.cluster_job.output() + '</pre>'
                self.output_field.value = html
        elif status['status'] == 'running':
            self.finished = False
            self.waiting_done()
            self.set_running(status['done'])
        elif status['status'] == 'waiting':
            self.finished = False
            self.set_waiting(status['done'])
            self.set_running(0.0)
        else:
            self.finished = False
            self.set_waiting(0.0)
            self.set_running(0.0)
        self.status_field.value = status['status']

    def running_done(self):
        self.running_progress.value = 1.0
        self.running_progress.bar_style = 'success'

    def set_running(self, value):
        self.running_progress.value = value
        self.running_progress.bar_style = 'info'

    def waiting_done(self):
        self.waiting_progress.value = 1.0
        self.waiting_progress.bar_style = 'success'

    def set_waiting(self, value):
        self.waiting_progress.value = value
        self.waiting_progress.bar_style = 'info'

    def wait(self):
        time.sleep(self.sleep_seconds)
