#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint: disable=C0111,W6005,W6100
"""
Package metadata for django-sodar-core.
"""
import os
from setuptools import setup

import versioneer

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))


def load_requirements(*requirements_paths):
    """
    Load all requirements from the specified requirements files.

    Returns:
        list: Requirements file relative path strings
    """
    requirements = set()
    for path in requirements_paths:
        requirements.update(
            line.split('#')[0].strip()
            for line in open(path).readlines()
            if is_requirement(line.strip())
        )
    return list(requirements)


def is_requirement(line):
    """
    Return True if the requirement line is a package requirement.

    Returns:
        bool: True if the line is not blank, a comment, a URL, or an included
              file
    """
    return not (
        line == ''
        or line.startswith('-r')
        or line.startswith('#')
        or line.startswith('-e')
        or line.startswith('git+')
    )


README = open(os.path.join(os.path.dirname(__file__), 'README.rst')).read()

setup(
    name='django-sodar-core',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="""SODAR Core framework and project management apps""",
    long_description=README,
    long_description_content_type='text/x-rst',
    author='Berlin Institute of Health, Core Unit Bioinformatics',
    author_email='cubi@bih-charite.de',
    url='https://github.com/bihealth/sodar-core',
    packages=[
        'projectroles',
        'adminalerts',
        'appalerts',
        'bgjobs',
        'filesfolders',
        'siteinfo',
        'sodarcache',
        'taskflowbackend',
        'timeline',
        'tokens',
        'userprofile',
    ],
    include_package_data=True,
    install_requires=load_requirements('requirements/base.txt'),
    zip_safe=False,
    classifiers=[
        'Framework :: Django',
        'Framework :: Django :: 3.2',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    python_requires='>=3.8',
)
