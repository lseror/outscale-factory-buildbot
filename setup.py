from setuptools import setup, find_packages

scripts = []
scripts.append('find_images=outscale_factory_buildbot.tools.find_images:main')
scripts.append('get_image=outscale_factory_buildbot.tools.get_image:main')
scripts.append('delete_images=outscale_factory_buildbot.tools.delete_images:main')
scripts.append('gen_password=outscale_factory_buildbot.tools.gen_password:main')
scripts.append('create_appliance_list=outscale_factory_buildbot.tools.create_appliance_list:main')

setup(
    name='outscale_factory_buildbot',
    version='0.1',
    description='Buildmaster support package',
    url='http://github.com/nodalink/outscale-factory-buildbot',
    author='Vincent Crevot',
    author_email=None,
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    entry_points=dict(console_scripts=scripts),
    install_requires=['boto'],
)
