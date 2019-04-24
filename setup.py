# pylint: disable=missing-docstring

# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from setuptools import setup


def get_long_description():
    with open('README.rst', 'r') as file:
        return file.read()


def get_install_requires(path):
    requires = []

    with open(path, 'r') as file:
        for line in file:
            if line.startswith('-r '):
                continue
            requires.append(line.strip())
        return requires


setup(
    name='kiwitcms-github-marketplace',
    version='0.1.0',
    description='GitHub Marketplace integration for Kiwi TCMS',
    long_description=get_long_description(),
    author='Kiwi TCMS',
    author_email='info@kiwitcms.org',
    url='https://github.com/kiwitcms/github-marketplace/',
    license='GPLv3+',
    install_requires=get_install_requires('requirements.txt'),
    packages=['tcms_github_marketplace'],
    include_package_data=True,
    classifiers=[
        'Framework :: Django',
        'Development Status :: 5 - Production/Stable',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Software Development :: Testing',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
    ],
)
