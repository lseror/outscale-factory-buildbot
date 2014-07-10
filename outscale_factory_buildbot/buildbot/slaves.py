"""
Buildslaves configuration.
"""
import boto

# from buildbot.buildslave.ec2 import EC2LatentBuildSlave
from buildbot.ec2buildslave import EC2LatentBuildSlave

from outscale_factory_buildbot.tools.gen_password import generate_password
from outscale_factory_buildbot.tools.get_image import get_image_id


BOTO_ERROR_MSG = """
AWS credentials missing from Boto config file!
Run turnkey-init or see
http://boto.readthedocs.org/en/latest/boto_config_tut.html
"""


def configure_buildslaves(c, fc, repos, meta):
    """
    Configure buildslaves.
    """
    # Buildmaster address
    master_address = meta['public-ipv4']

    # AWS credentials
    aws_id = boto.config.get('Credentials', 'aws_access_key_id')
    aws_key = boto.config.get('Credentials', 'aws_secret_access_key')
    assert aws_id and aws_key, BOTO_ERROR_MSG

    # AWS settings
    region = fc['region']
    keypair = fc['keypair']
    security_group = fc['security_group']

    # Slave count
    repo_count = len(repos)
    max_instances = fc['max_instances']
    slave_instance_count = min(repo_count, max_instances)

    # Slave instance settings
    slave_size = fc['slave_instance_size']
    slave_image = get_image_id(
        region,
        fc['slave_instance_ami_pattern'],
        fc['slave_instance_ami_tags'])

    # 'slavePortnum' defines the TCP port to listen on for connections from slaves.
    # This must match the value configured into the buildslaves (with their
    # --master option)
    c['slavePortnum'] = 9989

    # The 'slaves' list defines the set of recognized buildslaves. Each element is
    # a BuildSlave object, specifying a unique slave name and password.  The same
    # slave name and password must be configured on the slave.
    c['slaves'] = []

    for slave_id in range(0, slave_instance_count):
        slave_name = 'buildslave_{:03d}'.format(slave_id)
        slave_password = generate_password()

        slave_user_data = '\n'.join((
            master_address,
            slave_name,
            slave_password))

        c['slaves'].append(
            EC2LatentBuildSlave(
                slave_name,
                slave_password,
                slave_size,
                ami=slave_image,
                identifier=aws_id,
                secret_identifier=aws_key,
                region=region,
                keypair_name=keypair,
                security_name=security_group,
                user_data=slave_user_data,
            ))
