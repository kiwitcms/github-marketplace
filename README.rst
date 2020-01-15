GitHub Marketplace integration for Kiwi TCMS
============================================

.. image:: https://travis-ci.org/kiwitcms/github-marketplace.svg?branch=master
    :target: https://travis-ci.org/kiwitcms/github-marketplace

.. image:: https://coveralls.io/repos/github/kiwitcms/github-marketplace/badge.svg?branch=master
   :target: https://coveralls.io/github/kiwitcms/github-marketplace?branch=master

.. image:: https://pyup.io/repos/github/kiwitcms/github-marketplace/shield.svg
    :target: https://pyup.io/repos/github/kiwitcms/github-marketplace/
    :alt: Python updates

.. image:: https://tidelift.com/badges/package/pypi/kiwitcms-github-marketplace
    :target: https://tidelift.com/subscription/pkg/pypi-kiwitcms-github-marketplace?utm_source=pypi-kiwitcms-github-marketplace&utm_medium=github&utm_campaign=readme
    :alt: Tidelift

.. image:: https://opencollective.com/kiwitcms/tiers/sponsor/badge.svg?label=sponsors&color=brightgreen
   :target: https://opencollective.com/kiwitcms#contributors
   :alt: Become a sponsor

.. image:: https://img.shields.io/twitter/follow/KiwiTCMS.svg
    :target: https://twitter.com/KiwiTCMS
    :alt: Kiwi TCMS on Twitter

Introduction
------------

This package provides the GitHub Marketplace integration for the
`Kiwi TCMS multi-tenant SaaS <https://github.com/marketplace/kiwi-tcms>`_.
Everyting that we do is open and that's why this piece of code is
open source as well. You don't need this add-on in order to run Kiwi TCMS!

Changelog
---------

v0.8.1 (15 Jan 2020)
~~~~~~~~~~~~~~~~~~~~

- Replace ``ugettext_lazy`` with ``gettext_lazy`` for Django 3.0


v0.8 (07 Jan 2020)
~~~~~~~~~~~~~~~~~~

- Compatible with PyGithub v1.45+ which will be used in the upcoming
  Kiwi TCMS v7.3


v0.7.4 (08 Dec 2019)
~~~~~~~~~~~~~~~~~~~~

- ``utils.verify_signature()`` moved to ``tcms.utils.github`` as of
  Kiwi TCMS v7.2
- flake8 & pylint fixes


v0.7.3 (02 Nov 2019)
~~~~~~~~~~~~~~~~~~~~

- Fix a bug in reading pricing info when renewing subscriptions
  via FastSpring

v0.7.2 (29 May 2019)
~~~~~~~~~~~~~~~~~~~~

- Show vendor specific cancel URL
- Don't crash when revoking GitHub tokens
- Update subscription link via FastSpring


v0.7.1 (25 May 2019)
~~~~~~~~~~~~~~~~~~~~

- Handle purchases from FastSpring
- ``Purchase.sender`` is now an ``EmailField``


v0.6.0 (16 May 2019)
~~~~~~~~~~~~~~~~~~~~

- Handle purchases for organizations
- Do no use ``next_billing_date`` and use ``effective_date``
  when calculating ``paid_until``


v0.5.1 (16 May 2019)
~~~~~~~~~~~~~~~~~~~~

- Use the new ``delete_user()`` function when cancelling subscriptions
- Extend UI card in subscription page to 6 columns b/c long URL


v0.5.0 (15 May 2019)
~~~~~~~~~~~~~~~~~~~~

- Handle recurring purchases
- Don't crash if visiting Create Tenant without a purchase
- Show tenants which user can access and which they own
- Show purchase history with Buy/Cancel buttons
- Use ``prism.js`` for syntax highlighting
- Add translation files


v0.4.1 (08 May 2019)
~~~~~~~~~~~~~~~~~~~~

- Don't crash if install URL is visited without purchase
- Add Purchase admin, accessible only to superuser
- [db] Rename ``marketplace_purchase`` field to ``payload`` and
  add ``vendor`` field to ``Purchase`` model
- Add a view which overrides tenant creation with information
  from the latest purchase. This is what users will see when creating
  their private tenants
- When creating Private Tenant try to correctly set ``paid_until`` date
  based on ``next_billing_date`` or ``billing_cycle`` fields in the payload
  sent to us by GitHub


v0.3.1 (03 May 2019)
~~~~~~~~~~~~~~~~~~~~

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
