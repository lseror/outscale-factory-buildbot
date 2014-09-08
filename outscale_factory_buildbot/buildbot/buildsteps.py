"""
Custom build steps used to create a TurnKey appliance.

The module is an asynchronous wrapper over create_ami, which does
volume management and image creation operations synchronously with Boto.
"""

import logging
from datetime import datetime

import boto.ec2

from twisted.python import failure
from twisted.internet import threads, defer

from buildbot.status import results
from buildbot.process.buildstep import BuildStep
# from buildbot.buildslave.ec2 import EC2LatentBuildSlave
from buildbot.ec2buildslave import EC2LatentBuildSlave

from outscale_factory_buildbot.tools.delete_images import delete_images
from outscale_factory_buildbot.tools.find_images import find_images
from outscale_image_factory import create_ami


class _EC2BuildStep(BuildStep):

    """
    Base class for all EC2 buildsteps.
    """

    def __init__(self,
                 region=None,
                 location=None,
                 volume_gib=10,
                 object_tags={'slave': 'slave'},
                 image_arch='x86_64',
                 **kw):
        BuildStep.__init__(self, **kw)
        if region is None or location is None:
            raise TypeError("Required arguments: region, location")
        self.region = region
        self.location = location
        self.volume_gib = volume_gib
        self.object_tags = object_tags
        self.image_arch = image_arch
        self.addFactoryArguments(
            region=region,
            location=location,
            volume_gib=volume_gib,
            object_tags=dict(object_tags),
            image_arch=image_arch)

    def _connect(self):
        """
        Connect to the cloud.
        """
        return boto.ec2.connect_to_region(self.region)

    def _timestamp(self):
        """
        Generate timestamp.
        """
        return datetime.now().strftime('%y%m%d_%H%M')


class AttachNewVolume(_EC2BuildStep):

    """
    Attach a new volume to the buildslave instance.
    """

    def __init__(self, **kw):
        _EC2BuildStep.__init__(self, **kw)

    @defer.inlineCallbacks
    def start(self):
        """
        Start the buildstep.
        """
        assert isinstance(self.buildslave, EC2LatentBuildSlave)
        instance_id = self.buildslave.instance.id
        volume_tags = dict(self.object_tags)
        volume_tags['timestamp'] = self._timestamp()

        conn = yield threads.deferToThread(self._connect)
        volume_id, device, error = yield threads.deferToThread(
            create_ami.attach_new_volume,
            conn,
            instance_id,
            self.volume_gib,
            self.location,
            volume_tags)

        self.setProperty('instance_id', instance_id)
        self.setProperty('volume_id', volume_id)
        self.setProperty('device', device)
        self.setProperty('volume_tags', volume_tags)

        if volume_id and not error:
            self.finished(results.SUCCESS)
        else:
            self.failed(failure.Failure(error))


class CreateImage(_EC2BuildStep):

    """
    Create image from the buildslave's build volume.
    """

    def __init__(self, appliance=None, repourl=None, **kw):
        _EC2BuildStep.__init__(self, **kw)
        if appliance is None:
            raise TypeError('appliance argument is required')
        if repourl is None:
            raise TypeError('repourl argument is required')
        self.appliance = appliance
        self.repourl = repourl
        self.addFactoryArguments(
            appliance=appliance,
            repourl=repourl)

    @defer.inlineCallbacks
    def start(self):
        """
        Start the buildstep.
        """
        appliance = self.appliance
        repourl = self.repourl
        branch = self.getProperty('branch')
        revision = self.getProperty('got_revision')
        volume_id = self.getProperty('volume_id')
        image_description = self.getProperty('description', default=None)
        image_tags = self.getProperty('custom_tags', default={})

        image_timestamp = self._timestamp()
        image_name = '_'.join((appliance, image_timestamp))
        image_tags.update(dict(
            timestamp=image_timestamp,
            appliance=appliance,
            repourl=repourl,
            branch=branch,
            revision=revision,
        ))

        conn = yield threads.deferToThread(self._connect)
        image_id, error = yield threads.deferToThread(create_ami.create_image,
                                                      conn,
                                                      image_name,
                                                      volume_id,
                                                      self.image_arch,
                                                      image_description,
                                                      image_tags)

        self.setProperty('image_id', image_id)
        self.setProperty('image_name', image_name)
        self.setProperty('image_tags', image_tags)

        if not error:
            self.finished(results.SUCCESS)
        else:
            self.failed(failure.Failure(error))


class DestroyVolume(_EC2BuildStep):

    """
    Destroy the build volume.
    """

    def __init__(self, **kw):
        _EC2BuildStep.__init__(self, **kw)

    @defer.inlineCallbacks
    def start(self):
        """
        Start the buildstep.
        """
        volume_id = self.getProperty('volume_id')
        conn = yield threads.deferToThread(self._connect)
        ok, error = yield threads.deferToThread(create_ami.destroy_volume,
                                                conn,
                                                volume_id)
        if ok:
            self.finished(results.SUCCESS)
        else:
            self.failed(failure.Failure(error))


class DestroyOldImages(_EC2BuildStep):

    """
    Destroy old versions of an appliance image
    """

    def __init__(self, appliance=None, maxApplianceVersions=None, **kw):
        _EC2BuildStep.__init__(self, **kw)
        if appliance is None:
            raise TypeError('appliance argument is required')
        if maxApplianceVersions is None:
            raise TypeError('maxApplianceVersions argument is required')
        self.appliance = appliance
        self.maxApplianceVersions = maxApplianceVersions
        self.addFactoryArguments(
            appliance=appliance,
            maxApplianceVersions=maxApplianceVersions)

    @defer.inlineCallbacks
    def start(self):
        ok, error = yield threads.deferToThread(self._destroy_old_images)
        if ok:
            self.finished(results.SUCCESS)
        else:
            self.failed(failure.Failure(error))

    def _destroy_old_images(self):
        ok = False
        error = None

        try:
            images = find_images(self.region, tags=dict(appliance=self.appliance))
            images.sort(key=lambda x: x.tags['timestamp'])
            ids = [each.id for each in images[:-self.maxApplianceVersions]]
            delete_images(self.region, ids)
            ok = True

        except (boto.exception.BotoClientError,
                boto.exception.BotoServerError) as error:
            ok = False

        if error:
            logging.error('Could not destroy old images: {}'.format(error))

        return ok, error
