"""
Builders configuration
"""
import shlex

from buildbot.process.factory import BuildFactory
from buildbot.steps.source.git import Git
from buildbot.steps.shell import ShellCommand
from buildbot.process.properties import Property
from buildbot.config import BuilderConfig

from outscale_factory_buildbot.buildbot import buildsteps


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

        factory.addStep(ShellCommand(
            name='Building appliance',
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

        factory.addStep(ShellCommand(
            name='Cleaning up build dirs',
            alwaysRun=True,
            command=buildCmd + ['--clean-only'],
            env=buildEnv))

        buildername = '{}-{}'.format(appliance, branch)
        c['builders'].append(
            BuilderConfig(name=buildername,
                        slavenames=slavenames,
                        factory=factory,
                        mergeRequests=mergeRequests)
        )
