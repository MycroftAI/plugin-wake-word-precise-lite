from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'Precise Runner for Mycroft'
LONG_DESCRIPTION = 'Plugin module for Mycroft that supports Precise using tensorflow lite runtime'

def required(requirements_file):
    """Read requirements file and remove comments and empty lines."""
    base_dir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(base_dir, requirements_file), 'r') as f:
        requirements = f.read().splitlines()
        return [pkg for pkg in requirements
                if pkg.strip() and not pkg.startswith("#")]

setup(
    name="hotword_precise_lite",
    version=VERSION,
    author="MycroftAi",
    author_email="<noneofyour@business.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    entry_points={
        'mycroft.plugin.wake_word': 'hotword_precise_lite = hotword_precise_lite:TFLiteHotWord'},
    keywords=['mycroft', 'hot word', 'precise', 'lite', 'tensorflow'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developer",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Operating System :: LINUX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ],
    install_requires=required('requirements.txt')
)
