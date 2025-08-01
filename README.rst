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

- ``KIWI_GITHUB_PAT_FOR_CHECKING_ORGS_AND_USERNAMES`` - string
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

v4.2.6 (24 Jul 2025)
~~~~~~~~~~~~~~~~~~~~

- Update argument to ``tcms-profile`` URL, which was changed in Kiwi TCMS v14.3


v4.2.5 (22 May 2025)
~~~~~~~~~~~~~~~~~~~~

- Handle SKU references to hub.kiwitcms.eu Private Container Repository


v4.2.4 (08 May 2025)
~~~~~~~~~~~~~~~~~~~~

- Try harder to discover subscription price on Subscriptions page
- Don't crash if we can't extract display price for Subscriptions page


v4.2.2 (21 Apr 2025)
~~~~~~~~~~~~~~~~~~~~

- Bug fix: update exclude filter for Tenant Subscriptions page to account for
  subscription format with vendor prefix


v4.2 (27 Mar 2025)
~~~~~~~~~~~~~~~~~~

- Do not remove users from DB when they cancel their accounts.
  Let the account expire due to inactivity at which point it will
  be removed via cron job


v4.1.1 (16 Dec 2024)
~~~~~~~~~~~~~~~~~~~~

- Skip checking accounts which have been renewed or canceled meanwhile
- Don't hard-code the name of public schema


v4.1.0 (23 Nov 2024)
~~~~~~~~~~~~~~~~~~~~

- Check for recurring billing events for GitHub Marketplace b/c
  GitHub will not send a webhook for them


v4.0.4 (27 Oct 2024)
~~~~~~~~~~~~~~~~~~~~

- Return billing email for GitHub payloads when sender is null. Fixes
  a bug in processing webhooks from GitHub


v4.0.3 (22 Oct 2024)
~~~~~~~~~~~~~~~~~~~~

- Fix a bug in the Subscriptions page when subscription ID is None


v4.0.2 (22 Oct 2024)
~~~~~~~~~~~~~~~~~~~~

- Bug-fix: solve a crash when applying migrations/0011


v4.0.1 (20 Oct 2024)
~~~~~~~~~~~~~~~~~~~~

- Bug-fix: remove Quay.io account based on Purchase.subscription when handling
  cancelled subscriptions instead of using sender's email address


v4.0.0 (18 Oct 2024)
~~~~~~~~~~~~~~~~~~~~

- Automatically create a user account when someone purchases a paid subscription.
  Senders can reset their passwords and still be able to login if they wish to or
  use OAuth login!
- Use ``Purchase.subscription`` instead of ``Purchase.sender`` when creating
  Quay.io accounts, including a database migration for historical records.
  This means that Quay.io accounts are now numerical, instead of based on email
  addresses
- Record subscription_id for GitHub events in the format
  ``gh-<user-id>-<user|organization ID>``
- Prefix manual purchases subscription_id with ``man-``
- Prefix FastSpring subscription_id with ``fs-``, including a database migration
  for historical records
- Consider a GitHub purchase as activated only when price > 0 which fixes a
  side effect bug which was creating a Quay.io account for users who
  "purchased" the FREE plan on GitHub Marketplace
- Refactor ``GitHub.action_is_recurring_billing()``


v3.0.0 (07 Jun 2024)
~~~~~~~~~~~~~~~~~~~~

- Relicense this package under GNU Affero General Public License v3 or later
- Prior versions are still licensed under GNU General Public License v3


v2.6.0 (16 May 2024)
~~~~~~~~~~~~~~~~~~~~

- Require a new setting ``KIWI_GITHUB_PAT_FOR_CHECKING_ORGS_AND_USERNAMES``
- Add ``Purchase.gitops_prefix`` field with a new DB migration
- Record ``Purchase.gitops_prefix`` upon receiving incoming billing events
  from GitHub
- Allow the Subscription page to edit the new ``gitops_prefix`` field
- Add the ``GitOps.allow()`` API method for usage in ``kiwitcms/gitops``
- Replace inline style attributes with CSS classes


v2.5.1 (06 May 2024)
~~~~~~~~~~~~~~~~~~~~

- Adjust name of settings for ``revoke_oauth_token()`` to match production
  environment
- Adjust arguments for newer versions of PyGithub


v2.5.0 (03 May 2024)
~~~~~~~~~~~~~~~~~~~~

- Allow edits to ``Tenant.extra_emails`` field by overriding the HTML templates
  so we can expose this inside the UI. This new field is shown when creating
  a new tenant or editing an existing one
- FastSpring webhooks handler will also try matching the
  ``Tenant.extra_emails`` field before updating the expiration period.
  This will handle the situation where ``Tenant.owner`` is no longer the one
  who pays for the subscription
- Pin transitive dependencies to reduce the possibility of installing
  vulnerable packages
- Fix potentially uninitilized local variable
- Start using psycopg 3 for testing


v2.4.0 (13 Jan 2024)
~~~~~~~~~~~~~~~~~~~~

- Build and test with Python 3.11 & fix an import error
- Update key name for error responses from Quay.io
- Start testing with upstream Postgres container image, v16 currently.
  Note that installing ``btree_gin`` extension is commented out inside
  ``tcms_github_marketplace/migrations/0001_initial.py``


v2.3.8 (24 Aug 2023)
~~~~~~~~~~~~~~~~~~~~

- Fix a potential crash inside the Subscriptions page


v2.3.7 (23 Jun 2023)
~~~~~~~~~~~~~~~~~~~~

- Update mailchimp3 from 3.0.18 to 3.0.21


v2.3.6 (23 May 2023)
~~~~~~~~~~~~~~~~~~~~

- Try harder not to crash when handling non-recurring events from FastSpring
- Force ``None`` value for SKU to be evaluated as empty string


v2.3.3 (21 May 2023)
~~~~~~~~~~~~~~~~~~~~

- Handle expiration of unpaid requests for add-on services
- Unpin version for requests library to avoid potential conflicts
  with other add-ons


v2.3.2 (28 Apr 2023)
~~~~~~~~~~~~~~~~~~~~

- Update requests from 2.28.2 to 2.29.0
- Don't fail when trying to delete user after subscription has been cancelled


v2.3.1 (17 Apr 2023)
~~~~~~~~~~~~~~~~~~~~

- Discover billing cycle info from FastSpring subscription data
- Update mailchimp3 from 3.0.17 to 3.0.18


v2.3.0 (14 Apr 2023)
~~~~~~~~~~~~~~~~~~~~

- Add Admin interface so we can 'Approve' manual purchases
- Display both monthly & yearly price columns in admin panel
- Refactor by using a generic purchase notification handling workflow class
- Add preliminary support for yearly subscriptions on FastSpring by removing
  hard-coded values
- Add more tests


v2.2.0 (07 Apr 2023)
~~~~~~~~~~~~~~~~~~~~

- Fix fallback typo for FastSpring SKUs
- Adjust the fallback match string for Kiwi TCMS Enterprise on FastSpring
- Update requests from 2.28.1 to 2.28.2
- Adjust callbacks for newer PyGithub
- Reformat files with Black
- Don't raise general exceptions


v2.1.0 (15 Aug 2022)
~~~~~~~~~~~~~~~~~~~~

- Send an exit poll after a subscription has been cancelled
- Add filters to Purchase admin page
- Match username with email address for GitHub hooks too
- Add Purchase.subscription field
- Record subscription ID and search FastSpring tenants across
  all possible billing emails


v2.0.5 (04 Aug 2022)
~~~~~~~~~~~~~~~~~~~~

- Fix a 500 error because of missing prism.js
- Update requests from 2.27.1 to 2.28.1
- Bump versions for the rest of eslint plugins
- Adjust pylint options b/c of newer version
- Report test results to Kiwi TCMS


v2.0.4 (19 Apr 2022)
~~~~~~~~~~~~~~~~~~~~

- Add more tests related to tenant groups
- Require kiwitcms-tenants>=2.0
- Update GitHub actions & pre-commit hook versions


v2.0.3 (02 Mar 2022)
~~~~~~~~~~~~~~~~~~~~

- Fallback to searching by name instead of SKU for FastSpring because
  the SKU field isn't reliably sent for existing subscribers.


v2.0.2 (24 Feb 2022)
~~~~~~~~~~~~~~~~~~~~

- Add help block pointing to instructions for private containers
  at the bottom of the Docker credentials card


v2.0.1 (23 Feb 2022)
~~~~~~~~~~~~~~~~~~~~

- Add 2 new fields to ``Purchase`` model in database to hold information
  about enabled product features
- Automatically configure product access via FastSpring SKUs or GitHub
  Marketplace bullet items
- Properly handle cancelled and deactivated subscriptions, removing user
  accounts when needed
- Automatically handle docker accounts on Quay.io when a subscriotion is made
  and display them on the subscription page
- Display the 2 new fields in Purchase admin
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
