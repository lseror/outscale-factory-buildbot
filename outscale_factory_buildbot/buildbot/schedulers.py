"""
Scheduler configuration
"""

from buildbot.schedulers.basic import SingleBranchScheduler
from buildbot.schedulers.forcesched import ForceScheduler
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

    builderNames = ['appliance_builder']

    c['schedulers'] = []
    c['schedulers'].append(ForceScheduler(
        name="force",
        builderNames=builderNames))

    treeStableTimer = fc.get('tree_stable_timer_seconds', 120)
    enableNightlyScheduler = fc.get('nightly_scheduler', False)
    if enableNightlyScheduler:
        crontab = _parse_crontab_record(fc['nightly_crontab'])

    # For some reason the nightly scheduler does not set the *repository* property.
    # We cannot set it ourselves either.
    # Set a custom repourl property and use it later in the buildsteps.

    for appliance, repourl, branch in repos:
        name = '-'.join((appliance, branch))
        properties = dict(
            appliance=appliance,
            repourl=repourl
        )
        change_filter = filter.ChangeFilter(
            project=appliance,
            branch=branch
        )

        c['schedulers'].append(SingleBranchScheduler(
            name=name,
            builderNames=builderNames,
            change_filter=change_filter,
            properties=properties,
            treeStableTimer=treeStableTimer,
        ))

        if enableNightlyScheduler:
            nightlyName = 'nightly-{}'.format(name)
            c['schedulers'].append(timed.Nightly(
                name=nightlyName,
                builderNames=builderNames,
                branch=branch,
                change_filter=change_filter,
                properties=properties,
                minute=crontab[0],
                hour=crontab[1],
                dayOfMonth=crontab[2],
                month=crontab[3],
                dayOfWeek=crontab[4],
                onlyIfChanged=False,
                onlyImportant=False,
                fileIsImportant=None,
            ))
