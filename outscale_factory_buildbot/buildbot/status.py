"""
Status targets config
"""
from buildbot.status import html
from buildbot.status.web import authz, auth


def configure_status(c, fc, repos, meta):
    # STATUS TARGETS
    # 'status' is a list of Status Targets. The results of each build will be
    # pushed to these targets. buildbot/status/*.py has a variety to choose from,
    # including web pages, email senders, and IRC bots.
    c['status'] = []
    login = fc['web_status_login']
    password = fc['web_status_password']
    http_port = fc['web_status_listen_port']
    # Buildbot chokes on unicode credentials
    login = login.encode('ascii')
    password = password.encode('ascii')
    authz_cfg = authz.Authz(
        auth=auth.BasicAuth([(login, password)]),
        gracefulShutdown=False,
        forceBuild='auth',
        forceAllBuilds='auth',
        pingBuilder='auth',
        stopBuild='auth',
        stopAllBuilds='auth',
        cancelPendingBuild='auth',
    )
    c['status'].append(html.WebStatus(
        http_port=http_port,
        authz=authz_cfg,
        change_hook_dialects=dict(base=True),
    ))

    # PROJECT IDENTITY

    # the 'buildbotURL' string should point to the location where the buildbot's
    # internal web server (usually the html.WebStatus page) is visible. This
    # typically uses the port number set in the Waterfall 'status' entry, but
    # with an externally-visible host name which the buildbot cannot figure out
    # without some help.

    hostname = meta['public-hostname']
    c['buildbotURL'] = "http://{}:{}/".format(hostname, http_port)

    # the 'title' string will appear at the top of this buildbot
    # installation's html.WebStatus home page (linked to the
    # 'titleURL') and is embedded in the title of the waterfall HTML page.

    c['title'] = fc.get('project_title', "Turnkey Linux Factory")
    c['titleURL'] = c['buildbotURL']
