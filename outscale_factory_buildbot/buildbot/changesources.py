"""
Changesources configuration
"""
from buildbot.changes.gitpoller import GitPoller


def configure_changesources(c, fc, repos, meta):
    # the 'change_source' setting tells the buildmaster how it should find out
    # about source code changes.
    c['change_source'] = []
    pollinterval = fc['git_poll_interval_seconds']

    for appliance, repourl, branch in repos:
        workdir = 'gitpoller-{}'.format(appliance)
        c['change_source'].append(GitPoller(
            repourl=repourl,
            project=appliance,
            workdir=workdir,
            branch=branch,
            pollinterval=pollinterval
        ))
