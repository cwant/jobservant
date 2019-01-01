# jobservant

This package submits and monitors the progress of jobs on HPC clusters.

Expanded documentation comming soon, but currently there are three main classes: `jobservant.cluster_account.CluserAccount`, `jobservant/cluster_job.ClusterJob`, and `jobservant.jupyter.job_progress.JobProgress`.

## Demos

Checkout the Jupyter notebook demos in the `demo` directory. You should run your notebooks inside an SSH agent with keys loaded. There are two environment variables you might want to set before running your notebooks:

* `JOBSERVANT_CLUSTER`: the network name of the cluster you are connecting to.
* `JOBSERVANT_ACCOUNTING_GROUP`: the Slurm accounting group you will be using to submit jobs.

The individual notebooks will outline any additional requirements that may be needed.
