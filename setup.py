from setuptools import setup

with open('README.md') as f:
    readme_md = f.read()

setup(
    name='xplane_airports',
    version='0.0.1',
    packages=['env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.idna', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.pytoml', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.certifi', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.chardet', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.chardet.cli', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.distlib', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.distlib._backport', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.msgpack', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.urllib3',
              'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.urllib3.util', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.urllib3.contrib', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.urllib3.contrib._securetransport', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.urllib3.packages', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.urllib3.packages.backports', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.urllib3.packages.ssl_match_hostname', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.colorama', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.html5lib', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.html5lib._trie', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.html5lib.filters',
              'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.html5lib.treewalkers', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.html5lib.treeadapters', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.html5lib.treebuilders', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.lockfile', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.progress', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.requests', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.packaging', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.cachecontrol', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.cachecontrol.caches', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.webencodings',
              'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._vendor.pkg_resources', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._internal', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._internal.req', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._internal.vcs', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._internal.utils', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._internal.models', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._internal.commands', 'env.lib.python3.7.site-packages.pip-10.0.1-py3.7.egg.pip._internal.operations', 'xplane_airports'],
    url='https://github.com/X-Plane/xplane_airports',
    license='MIT',
    author='Tyler Young',
    author_email='tyler@x-plane.com',
    description='Tools for manipulating X-Plane\'s apt.dat files & interfacing with the X-Plane Scenery Gateway',
    long_description=readme_md,
    long_description_content_type="text/markdown",
)
