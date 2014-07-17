"""
Subpackage used by the buildbot master server.

Functions in this subpackage generally look like:
     configure_something(c, fc, repos, meta)

Arguments are:
    c: buildmaster config
    fc: factory config
    repos: list of git repos
    meta: buildmaster instance metadata
"""
from . import builders
from . import changesources
from . import config
from . import db
from . import log
from . import schedulers
from . import slaves
from . import status
