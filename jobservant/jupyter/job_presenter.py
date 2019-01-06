from .job_progress import JobProgress
from .job_status_table import JobStatusTable


class JobPresenter:

    def __init__(self, cluster_job, **kwargs):
        self.cluster_job = cluster_job

    def progress(self, **kwargs):
        progress = JobProgress(self.cluster_job, **kwargs)
        progress.run_in_background()

    def status_table(self, **kwargs):
        status_table = JobStatusTable(self.cluster_job, **kwargs)
        status_table.run()
