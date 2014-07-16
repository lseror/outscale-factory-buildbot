"""
DB configuration
"""


def configure_db(c, fc, repos, meta):
    # This specifies what database buildbot uses to store its state.  You can leave
    # this at its default for all but the largest installations.
    c['db'] = {
        'db_url': "sqlite:///state.sqlite",
    }
