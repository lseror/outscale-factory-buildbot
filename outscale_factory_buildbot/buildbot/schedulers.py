"""
Scheduler configuration
"""

from buildbot.schedulers.basic import SingleBranchScheduler
from buildbot.schedulers.forcesched import ForceScheduler, FixedParameter
from buildbot.schedulers import timed
from buildbot.changes import filter


def _parse_crontab_record(crontab):
    """
    Parse a crontab-like record.

    Format: 5 fields separated by spaces.
    The fields are: minute hour dayofmonth month dayofweek.
    The values can either be integers or the '*' wildcard.
    """
    parsed = []
    for field in crontab.split(' '):
        try:
            parsed.append(int(field))
        except ValueError:
            assert field == '*'
            parsed.append(field)
    assert len(parsed) == 5
    return parsed


def configure_schedulers(c, fc, repos, meta):
    # Configure the Schedulers, which decide how to react to incoming changes.

    c['schedulers'] = []

    treeStableTimer = fc.get('tree_stable_timer_seconds', 120)
    enableNightlyScheduler = fc.get('nightly_scheduler', False)
    if enableNightlyScheduler:
        crontab = _parse_crontab_record(fc['nightly_crontab'])

    for appliance, repourl, branch in repos:
        name = '-'.join((appliance, branch))
        builderNames = [name]
        c['schedulers'].append(ForceScheduler(
            name='force-{}'.format(name),
            builderNames=builderNames,
            revision=FixedParameter(name="revision", default=""),
            repository=FixedParameter(name="repository", default=""),
            project=FixedParameter(name="project", default=""),
            branch=FixedParameter(name="branch", default=branch),
            properties=[],
        ))

        change_filter = filter.ChangeFilter(
            project=appliance,
            branch=branch
        )

        c['schedulers'].append(SingleBranchScheduler(
            name='onchanges-{}'.format(name),
            builderNames=builderNames,
            change_filter=change_filter,
            treeStableTimer=treeStableTimer,
        ))

        if enableNightlyScheduler:
            c['schedulers'].append(timed.Nightly(
                name='nightly-{}'.format(name),
                builderNames=builderNames,
                branch=branch, # Nightly requires a 'branch' argument
                change_filter=change_filter,
                minute=crontab[0],
                hour=crontab[1],
                dayOfMonth=crontab[2],
                month=crontab[3],
                dayOfWeek=crontab[4],
                onlyIfChanged=False,
                onlyImportant=False,
                fileIsImportant=None,
            ))
