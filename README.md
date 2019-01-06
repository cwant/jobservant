# jobservant

[![Build Status](https://travis-ci.org/cwant/jobservant.svg?branch=master)](https://travis-ci.org/cwant/jobservant)

This package submits and monitors the progress of jobs on HPC clusters.

Expanded documentation coming soon, but currently there are three main classes: `jobservant.cluster_account.ClusterAccount`, `jobservant.cluster_job.ClusterJob`, and `jobservant.jupyter.job_display.JobDisplay`.

## Demos

Checkout the Jupyter notebook demos in the `demo` directory. You should run your notebooks inside an SSH agent with keys loaded. There are two environment variables you might want to set before running your notebooks:

* `JOBSERVANT_CLUSTER`: the network name of the cluster you are connecting to.
* `JOBSERVANT_ACCOUNTING_GROUP`: the Slurm accounting group you will be using to submit jobs.

The individual notebooks will outline any additional requirements that may be needed.

## My setup

`jobservant` relies on a package called `paramiko` to handle SSH communication between the remote cluser and your computer. In order for this work, we need to set up some SSH keys to work via an ssh agent. Here are pretty much all of the steps that I would take (using Linux/Mac) to get the whole thing working. This is not the only way to get things working, but it's the way I would set things up.

### SSH setup

* Create an SSH key if you don't already have one. This is done with the command `ssh-keygen -t rsa`. By default, this will create a private key in the file `~/.ssh/id_rsa` and a public key in `~/.ssh/id_rsa.pub`. For the sake of security, please give your private key a passphrase when prompted to do so (otherwise, if your computer is compromised, intruders may also get access to the remote cluster).
* Put the public key in the file `~/.ssh/authorized_keys` on the remote cluster. That is, put the contents of `id_rsa.pub` in that file on the remote machine -- DO NOT put your private key (`id_rsa`) there!
* Start an SSH agent on your computer. An SSH needs a (usually interactive) program to run in. My preference is to run it in `tmux`, but you could also run it in `bash` if you like. So we do either `ssh-agent tmux` or `ssh-agent bash` at the command line.
* Add your keys to the agent by running `ssh-add` in the program your agent is running in (`tmux` or `bash`). You will be prompted to supply the passphrase you used when creating your SSH key. Your SSH key is now ready to use, and you can SSH to the remote cluster without a password within either `tmux` or `bash`

### Python virtual enviroment

* I like to use python 3.7 currently, but probably python 3.5 or 3.6 will do.
* Create a python virtual environment on your computer using `virtualenv --no-download ~/virtualenv-jobservant`
* Activate the virtual environment with `source ~/virtualenv-jobservant`. (Your command line prompt should change.) All packages you install should be local to the virtual environment (not installed globally), and the virtual environment will be activated until you issue the command `deactivate` (don't do that now though).
* Install some packages: `pip3 install jupyter paramiko`
* For the K-Means clustering demo, you might want to install a few additional packages: `pip3 install numpy pandas matlplotlib sklearn`.

### Running Jupyter

* I don't like to hardcode server names or accounting groups in my notebooks, so instead I put them in environment variables  (this make it easier to switch clusters without modifying my notebooks). As mentioned above, the demos use the environment variables `JOBSERVANT_CLUSTER` and `JOBSERVANT_ACCOUNTING_GROUP` to set these (or if you really want, you can hardcode these in the notebooks instead -- it's up to you). With this in mind, here is how I start my jupyter notebook server:
  `JOBSERVANT_CLUSTER='foo.whatever.org' JOBSERVANT_ACCOUNTING_GROUP='gabba-gabba-hey' jupyter notebook`
* A browser should spawn for you, click on the `demo` directory and check things out.
