Marketplace integrations for Kiwi TCMS
======================================

.. image:: https://codecov.io/gh/kiwitcms/github-marketplace/branch/master/graph/badge.svg?token=NQKAQMJ8N8
    :target: https://codecov.io/gh/kiwitcms/github-marketplace
    :alt: Code coverage badge

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

This package provides the marketplace/payment integration for the
`Kiwi TCMS multi-tenant SaaS <https://kiwitcms.org/#subscriptions>`_.
Everyting that we do is open and that's why this piece of code is
open source as well. You don't need this add-on in order to run Kiwi TCMS!


Installation
------------

    pip install kiwitcms-github-marketplace


Configuration
-------------

Required settings:

- ``KIWI_GITHUB_MARKETPLACE_SECRET`` - binary string
- ``KIWI_FASTSPRING_SECRET`` - binary string
- ``QUAY_IO_TOKEN`` - string
- ``MAILCHIMP_USERNAME`` - string
- ``MAILCHIMP_SECRET`` - string

Product configuration
---------------------

- Subscriptions on FastSpring use the SKU field to define access to private
  docker repositories. The format is ``repo_name1+repo_name2``, where
  ``https://quay.io/kiwitcms/<repo_name>`` exists
- FastSpring SKUs starting with "x-" are considered special and we don't
  treat them as docker repository names
- Plans on GitHub Marketplace use one of their bullet items to define access
  to private docker repositories. Format is
  ``Docker repositories: quay.io/kiwitcms/<repo1>, quay.io/kiwitcms/<repo2>``


Changelog
---------

v2.0.0 (23 Feb 2022)
~~~~~~~~~~~~~~~~~~~~

- Add 2 new fields to ``Purchase`` model in database to hold information
  about enabled product features
- Automatically configure product access via FastSpring SKUs or GitHub
  Marketplace bullet items
- Properly handle cancelled and deactivated subscriptions, removing user
  accounts when needed
- Automatically handle docker accounts on Quay.io when a subscriotion is made
  and display them on the subscription page
- Ask subscribers to opt-in for newsletter
- Add more automated tests & CI tools


v1.7.0 (30 Sep 2021)
~~~~~~~~~~~~~~~~~~~~

- Search tenants either by owner email or username. Fixes an issue where
  some tenant owners use the billing email as their username, while
  changing the contact email in the Kiwi TCMS database
- Adjust for backwards incompatible changes in PyGithub 1.55
- Use f-strings


v1.6.0 (29 Aug 2021)
~~~~~~~~~~~~~~~~~~~~

- Fix a bug which allowed users to create multiple tenants
- Fix `Sentry #KIWI-TCMS-H2 <https://sentry.io/organizations/kiwitcms/issues/2584184445>`_
- Fix issues discovered by newest pylint
- Don't allow user to create multiple tenants if they refresh the page, e.g.
  after a 504 response. Instead redirect them to previously existing tenant
- Migrate from Travis CI to GitHub Actions
- Improvements of tests & CI


v1.5.0 (11 Jul 2021)
~~~~~~~~~~~~~~~~~~~~

- Test with Kiwi TCMS v10.1 or later
- Require kiwitcms-tenants>=1.5 in order to support public read-only tenants
- Migrate to Python 3.8
- Internal refactoring


v1.4.0 (03 Mar 2021)
~~~~~~~~~~~~~~~~~~~~

- Don't delete users upon cancellation via GitHub


v1.3.4 (18 Feb 2021)
~~~~~~~~~~~~~~~~~~~~

- Show new column in purchase admin
- Stop advertising GitHub Marketplace subscriptions


v1.3.3 (25 Jan 2021)
~~~~~~~~~~~~~~~~~~~~

- Allow POST request (web hooks) without CSRF token


v1.3.2 (26 Dec 2020)
~~~~~~~~~~~~~~~~~~~~

- Don't fail when cancelling GitHub FREE subscriptions for senders which
  don't exist


v1.3.1 (09 Dec 2020)
~~~~~~~~~~~~~~~~~~~~

- Fix traceback when trying to create tenant and user is not logged in


v1.3 (13 Sep 2020)
~~~~~~~~~~~~~~~~~~

- Tested with Kiwi TCMS > 8.6
- Refactor deprecation warnings with Django 3.1
- Start using the new standard models.JSONField()
- Remove ``tcms_settings_dir/marketplace.py`` b/c ``settings.PUBLIC_VIEWS``
  has been removed


v1.2 (06 Aug 2020)
~~~~~~~~~~~~~~~~~~

- Require kiwitcms-tenants>=1.1
- Subscribe button is now a drop-down listing all platforms oferring a
  Private Tenant subscription


v1.1 (24 Apr 2020)
~~~~~~~~~~~~~~~~~~

- Bug fix: display form errors when creating new tenant
- Update template strings


v1.0 (17 Mar 2020)
~~~~~~~~~~~~~~~~~~

- Turn into proper Kiwi TCMS plugin and install settings overrides under
  ``tcms_settings_dir/`` (compatible with Kiwi TCMS v8.2 or later):

  - does not need ``MENU_ITEMS`` and ``PUBLIC_VIEWS`` override anymore
  - does not need to load ``tcms_github_marketplace`` in ``INSTALLED_APPS``
    manually
- Jump over ``tcms_tenants.views.NewTenantView`` b/c it requires
  ``tcms_tenants.add_tenant`` permission and here we don't need that
- Exclude public tenant from recurring purchase hooks
- Do not attempt delete for superuser cancelling their tenant purchases


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
