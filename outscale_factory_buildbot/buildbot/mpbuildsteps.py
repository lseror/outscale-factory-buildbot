"""
Custom build steps used to communicate with the Marketplace.
"""
import logging
import json

from datetime import datetime

import dateutil.tz

import lam

from twisted.internet import threads, defer
from twisted.python import failure

from buildbot.process.buildstep import BuildStep
from buildbot.status import results
from buildbot.steps.shell import SetProperty


class FindPackageReferences(SetProperty):
    """
    Call find_package_references to list all package references in an appliance
    source. Stores the result in the `package_references` property.
    """
    def __init__(self,
                 srcdir=None,
                 **kw):
        if srcdir is None:
            raise TypeError('srcdir argument is required')

        kw.update(dict(
            command=['find_package_references', srcdir],
            extract_fn=self._extract_package_references,
            ))

        SetProperty.__init__(self, **kw)

        # This is necessary even if we don't use srcdir anywhere else because
        # Buildbot will instantiate a new FindPackageReferences instance at
        # build time, so it needs all the arguments to be able to do so.
        self.addFactoryArguments(srcdir=srcdir)

    @staticmethod
    def _extract_package_references(rc, stdout, stderr):
        if rc != 0:
            logging.error('find_package_references failed with error code {}'
                          .format(rc))
            return {}
        lst = json.loads(stdout)
        return {'package_references': lst}


class AddImageToMarketplace(BuildStep):
    """
    Send a message to the marketplace with the details of the new image
    """
    def __init__(self,
                 mpconfig=None,
                 appliance=None,
                 **kw):
        BuildStep.__init__(self, **kw)
        if mpconfig is None:
            raise TypeError('mpconfig argument is required')
        if appliance is None:
            raise TypeError('appliance argument is required')
        self.mpconfig = mpconfig
        self.appliance = appliance
        self.addFactoryArguments(
            mpconfig=mpconfig,
            appliance=appliance)

    @defer.inlineCallbacks
    def start(self):
        branch = self.getProperty('branch')
        image_id = self.getProperty('image_id')
        package_references = self.getProperty('package_references')
        ok, error = yield threads.deferToThread(self._add_image,
                                                branch,
                                                image_id,
                                                package_references)
        if ok:
            self.finished(results.SUCCESS)
        else:
            self.failed(failure.Failure(error))

    def _add_image(self, branch, image_id, package_references):
        ok = False
        error = None
        build_date = datetime.now(dateutil.tz.tzlocal())
        changelog = '' # TODO
        try:
            client = lam.Client('marketplace', self.mpconfig['amqp_url'])
            client.add_image(self.appliance, branch, image_id,
                             build_date.isoformat(), changelog,
                             package_references)
            ok = True
        except Exception as error:
            logging.exception('Failed to add image to marketplace')
            ok = False
        return ok, error
