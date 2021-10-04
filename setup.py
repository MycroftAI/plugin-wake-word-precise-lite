from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'Precise Runner for Mycroft'
LONG_DESCRIPTION = 'Plugin module for Mycroft that supports Precise using tensorflow lite runtime'

setup(
    name="hotword_precise_lite",
    version=VERSION,
    author="MycroftAi",
    author_email="<noneofyour@business.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[],
    dependency_links=[
        'https://google-coral.github.io/py-repo/ tflite_runtime'],
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
    ]
)
