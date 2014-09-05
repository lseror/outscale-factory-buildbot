"""
Builders configuration
"""
import shlex

from buildbot.process.factory import BuildFactory
from buildbot.steps.source.git import Git
from buildbot.steps.shell import ShellCommand
from buildbot.process.properties import Property
from buildbot.process import slavebuilder
from buildbot.config import BuilderConfig

from outscale_factory_buildbot.buildbot import buildsteps


def _choose_slave(builder, slave_builders):
    # Pick the slave_builder to use for a build, based on its state.
    # Prefer idle, then latent then building slaves.

    preferred_states = [
        slavebuilder.PINGING, # build about to start, making sure it is still alive
        slavebuilder.ATTACHING, # slave attached, still checking hostinfo/etc
        slavebuilder.SUBSTANTIATING,
        slavebuilder.BUILDING, # build is running
        slavebuilder.LATENT, # latent slave is not substantiated; similar to idle
        slavebuilder.IDLE, # idle, available for use
        ]

    best = None
    best_score = -1
    for sb in slave_builders:
        sb_score = preferred_states.index(sb.state)
        if sb_score > best_score:
            best = sb
            best_score = sb_score
    assert best
    return best


def configure_builders(c, fc, repos, meta):
    # The 'builders' list defines the Builders, which tell Buildbot how to perform a build:
    # what steps, and which slaves can execute them.  Note that any particular build will
    # only take place on one slave.

    ec2Args = dict(
        region=fc['region'],
        location=fc['location'],
        image_arch=fc.get('create_image_arch', 'x86_64'),
        volume_gib=fc.get('build_volume_gib', 10),
        object_tags=fc.get('slave_objects_tags', {'slave': 'slave'})
    )
    mountPoint = fc.get('slave_build_mount_point', '/mnt/%s')
    workDir = fc.get('slave_build_work_dir', '/srv/%s')
    baseBuildCmd = fc.get('slave_build_command', 'build_ami -v')
    baseBuildCmd = shlex.split(baseBuildCmd)
    masterAddr = 'http://' + meta['public-ipv4']
    aptProxyPort = fc.get('master_apt_proxy_port', 3142)
    httpProxyPort = fc.get('master_http_proxy_port', 8124)
    buildEnv = dict(
        FAB_APT_PROXY='{}:{}'.format(masterAddr, aptProxyPort),
        FAB_HTTP_PROXY='{}:{}'.format(masterAddr, httpProxyPort)
    )

    mergeRequests = fc.get('merge_build_requests', False)
    slavenames = [slave.slavename for slave in c['slaves']]

    c['builders'] = []
    for appliance, repourl, branch in repos:
        factory = BuildFactory()

        buildCmd = baseBuildCmd + [
            '--turnkey-app', appliance,
            '--device', Property('device'),
            '--mount-point', mountPoint % appliance,
            '--work-dir', workDir % appliance,
        ]

        factory.addStep(Git(
            name='Cloning repository',
            haltOnFailure=True,
            repourl=repourl,
            workdir='/turnkey/fab/products/{}'.format(appliance),
            mode='incremental',
            branch=branch,
            submodules=True))

        factory.addStep(buildsteps.AttachNewVolume(
            name='Creating build volume',
            haltOnFailure=True,
            **ec2Args))

        # ShellCommand fails if `description` is not set: it tries to
        # generate it from `command` but fails because `command`
        # contains a Property. To avoid this, set `description` to the
        # same value as `name`.
        name = 'Building appliance'
        factory.addStep(ShellCommand(
            name=name,
            description=name,
            descriptionDone='Appliance built',
            haltOnFailure=True,
            command=buildCmd + ['--build-only'],
            env=buildEnv))

        factory.addStep(buildsteps.CreateImage(
            name='Creating image',
            haltOnFailure=True,
            repourl=repourl,
            appliance=appliance,
            **ec2Args))

        factory.addStep(buildsteps.DestroyVolume(
            name='Cleaning up volume',
            alwaysRun=True,
            **ec2Args))

        name = 'Cleaning up build dirs'
        factory.addStep(ShellCommand(
            name=name,
            description=name,
            descriptionDone='Build dirs cleaned',
            alwaysRun=True,
            command=buildCmd + ['--clean-only'],
            env=buildEnv))

        buildername = '{}-{}'.format(appliance, branch)
        c['builders'].append(
            BuilderConfig(name=buildername,
                        slavenames=slavenames,
                        factory=factory,
                        mergeRequests=mergeRequests,
                        nextSlave=_choose_slave)
        )
