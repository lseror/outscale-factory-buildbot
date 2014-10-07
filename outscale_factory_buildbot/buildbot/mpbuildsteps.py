"""
Custom build steps used to communicate with the Marketplace.
"""
import logging

from datetime import datetime

import dateutil.tz

import lam

from twisted.internet import threads, defer
from twisted.python import failure

from buildbot.status import results
from buildbot.process.buildstep import BuildStep


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
        package_references = [] # FIXME self.getProperty('package_references')
        ok, error = yield threads.deferToThread(self._add_image, branch,
                                                image_id, package_references)
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
