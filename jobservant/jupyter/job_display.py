from .job_progress import JobProgress


class JobDisplay:

    def __init__(self, cluster_job, **kwargs):
        self.cluster_job = cluster_job

    def progress(self, **kwargs):
        progress = JobProgress(self.cluster_job, **kwargs)
        progress.run_in_background()
