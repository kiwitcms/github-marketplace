GitHub Marketplace integration for Kiwi TCMS
============================================

.. image:: https://travis-ci.org/kiwitcms/github-marketplace.svg?branch=master
    :target: https://travis-ci.org/kiwitcms/github-marketplace

.. image:: https://coveralls.io/repos/github/kiwitcms/github-marketplace/badge.svg?branch=master
   :target: https://coveralls.io/github/kiwitcms/github-marketplace?branch=master

.. image:: https://pyup.io/repos/github/kiwitcms/github-marketplace/shield.svg
    :target: https://pyup.io/repos/github/kiwitcms/github-marketplace/
    :alt: Python updates

.. image:: https://opencollective.com/kiwitcms/tiers/sponsor/badge.svg?label=sponsors&color=brightgreen
   :target: https://opencollective.com/kiwitcms#contributors
   :alt: Become a sponsor


Introduction
------------

This package provides the GitHub Marketplace integration for the
`Kiwi TCMS multi-tenant SaaS <https://github.com/marketplace/kiwi-tcms>`_.
Everyting that we do is open and that's why this piece of code is
open source as well. You don't need this add-on in order to run Kiwi TCMS!

Changelog
---------

v0.3.1 (03 May 2019)
~~~~~~~~~~~~~~~~~~~~~~

- Fix index name in models to be the same as in migrations


v0.3.0 (27 April 2019)
~~~~~~~~~~~~~~~~~~~~~~

- Handle Marketplace plan cancellations


v0.2.1 (27 April 2019)
~~~~~~~~~~~~~~~~~~~~~~

- Refactor how hooks and installation is handled. Now purchase info
  is stored in database and we search for it during installation
- Introduces database migrations
- Free plan purchases from Marketplace still redirect to Public Tenant


v0.1.1 (25 April 2019)
~~~~~~~~~~~~~~~~~~~~~~

- Handle GitHub hook pings


v0.1.0 (24 April 2019) - initial release
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Free plan purchases from Marketplace redirect to Public Tenant
