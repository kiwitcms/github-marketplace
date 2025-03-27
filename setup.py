# pylint: disable=missing-docstring

# Copyright (c) 2019-2025 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

from setuptools import setup, find_packages


def get_long_description():
    with open("README.rst", "r", encoding="utf-8") as file:
        return file.read()


def get_install_requires(path):
    requires = []

    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            if line.startswith("-r "):
                continue
            requires.append(line.strip())
        return requires


setup(
    name="kiwitcms-github-marketplace",
    version="4.2",
    description="GitHub Marketplace integration for Kiwi TCMS",
    long_description=get_long_description(),
    author="Kiwi TCMS",
    author_email="info@kiwitcms.org",
    url="https://github.com/kiwitcms/github-marketplace/",
    license="AGPLv3+",
    install_requires=get_install_requires("requirements.txt"),
    packages=find_packages(exclude=["test_project*", "*.tests"]),
    zip_safe=False,
    include_package_data=True,
    entry_points={"kiwitcms.plugins": ["github/marketplace = tcms_github_marketplace"]},
    classifiers=[
        "Framework :: Django",
        "Development Status :: 5 - Production/Stable",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.11",
    ],
)
