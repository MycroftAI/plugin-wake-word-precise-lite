import os
import sys
from setuptools import setup, find_packages
from setuptools.command.install import install as _install
from subprocess import call

VERSION = '0.0.1'
DESCRIPTION = 'Precise Runner for Mycroft'
LONG_DESCRIPTION = 'Plugin module for Mycroft that supports Precise using tensorflow lite runtime'

with open('README.md', 'r') as fh:
    long_description = fh.read()


class install(_install):
    """A custom install command class to execute post-install tasks."""

    def run(self):
        _install.run(self)
        self.execute(_post_install, (self.install_lib,),
                     msg='Running post install task')


def _post_install(dir):
    """Will be executed after installing the package."""
    call([sys.executable, '-m', 'pip', 'install', '--index-url',
         'https://google-coral.github.io/py-repo/', 'tflite_runtime~=2.5.0'])


def required(requirements_file):
    """Read requirements file and remove comments and empty lines."""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(base_dir, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith('#')]


setup(
    cmdclass={'install': install},
    name='hotword_precise_lite',
    version=VERSION,
    author='Mycroft AI',
    author_email='dev@mycroft.ai',
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    license=('Apache License 2.0'),
    packages=find_packages(),
    entry_points={
        'mycroft.plugin.wake_word': 'hotword_precise_lite = hotword_precise_lite:TFLiteHotWord'},
    keywords=['mycroft', 'wake word', 'hot word',
              'precise', 'lite', 'tensorflow'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Multimedia :: Sound/Audio :: Speech',
        'Topic :: Text Processing :: Linguistic',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Operating System :: LINUX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
    ],
    install_requires=required('requirements.txt')
)
