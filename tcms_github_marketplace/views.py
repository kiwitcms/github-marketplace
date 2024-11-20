# Copyright (c) 2019-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

# pylint: disable=missing-permission-required, no-self-use

import json
import os
from datetime import datetime

from django.db.models import Q
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse, reverse_lazy
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import View
from django.views.generic.edit import UpdateView
from django.utils.decorators import method_decorator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required

from tcms.core.utils.mailto import mailto
from tcms.utils import github

from django_tenants.utils import get_public_schema_name
from tcms_tenants.models import Tenant
from tcms_tenants.utils import create_user_account
from tcms_tenants.views import NewTenantView
from tcms_tenants import utils as tcms_tenants_utils

from tcms_github_marketplace import docker
from tcms_github_marketplace import fastspring
from tcms_github_marketplace import forms
from tcms_github_marketplace.github import find_sku as github_find_sku
from tcms_github_marketplace import mailchimp
from tcms_github_marketplace import utils
from tcms_github_marketplace.models import Purchase


UserModel = get_user_model()


class GenericPurchaseNotificationView(View):
    """
    Base handler of notification purchases defining common methods and workflow structure.
    Specific vendor views will inherit from this and override methods where necessary!
    """

    http_method_names = ["post", "head", "options"]
    purchase_vendor = None

    def action_is_activated(self, purchase):
        raise NotImplementedError

    def action_is_cancelled(self, purchase):
        raise NotImplementedError

    def action_is_recurring_billing(self, purchase):
        raise NotImplementedError

    def create_user_account(self, email):
        """
        Will create an account for whomever is purchasing this subscription!
        """
        if not UserModel.objects.filter(email=email).first():
            create_user_account(email)

    def find_paid_tenant(self, purchase):  # pylint: disable=unused-argument
        """
        Return a QuerySet which is possible to contain a pre-existing tenant
        which has been paid for by this Customer.

        Usually for the purpose of updating the `paid_util` field in case of
        recurring billing.

        WARNING: Calling environment will call `.first()` on this!

        WARNING: Vendor specific classes will inherit/override the result!
        """
        # the minimum implementation just returns all tenants that have been paid for
        return Tenant.objects.filter(
            paid_until__isnull=False,
        ).exclude(schema_name=get_public_schema_name())

    def find_sku(self, purchase):
        raise NotImplementedError

    def purchase_action(self, event):
        raise NotImplementedError

    def purchase_effective_date(self, event):
        raise NotImplementedError

    def purchase_gitops_prefix(self, event):  # pylint: disable=unused-argument
        return None

    def purchase_sender(self, event):
        raise NotImplementedError

    def purchase_should_have_tenant(self, event):
        raise NotImplementedError

    def purchase_subscription(self, event):  # pylint: disable=unused-argument
        return None

    def record_purchase(self, **kwargs):
        purchase = Purchase.objects.create(**kwargs)

        # remove possible stale state
        if purchase.gitops_prefix:
            cache.clear()

        return purchase

    def request_verify_signature(self, request):
        raise NotImplementedError

    def vendor_pre_process_payload(self, payload):  # pylint: disable=unused-argument
        """
        Perform any vendor specific pre-processing of payload before beginning
        the actual purchase flow. This is usually used to transform payload fields
        so they can match the existing implementation.
        """
        return payload

    def vendor_pre_process_request(
        self, request, payload
    ):  # pylint: disable=unused-argument
        """
        Perform any vendor specific pre-processing of request before beginning
        the actual purchase flow.

        Return HttpResponse if the flow should return back to the client!
        """
        return

    def vendor_response(self, purchase):  # pylint: disable=unused-argument
        """
        Returns the response from handling the payload!
        """
        return HttpResponse("ok", content_type="text/plain")

    def post(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        result = self.request_verify_signature(request)
        if result is not True:
            return result  # must be an HttpResponse then

        json_payload = json.loads(request.body.decode("utf-8"))

        response = (  # pylint: disable=assignment-from-none
            self.vendor_pre_process_request(request, json_payload)
        )
        if response:
            return response

        # NOTE: for vendors which don't support event batching the RAW data
        # should be transformed into a list!
        for event in self.vendor_pre_process_payload(json_payload):
            # first order of business is to record this into the database
            purchase = self.record_purchase(
                action=self.purchase_action(event),
                effective_date=self.purchase_effective_date(event),
                payload=event,
                sender=self.purchase_sender(event),
                should_have_tenant=self.purchase_should_have_tenant(event),
                subscription=self.purchase_subscription(event),
                vendor=self.purchase_vendor,
                gitops_prefix=self.purchase_gitops_prefix(event),
            )

            if self.action_is_cancelled(purchase):
                return utils.cancel_plan(purchase)

            if self.action_is_activated(purchase) and not os.environ.get(
                "SKIP_QUAY_IO", False
            ):
                # create an account for first time users
                self.create_user_account(purchase.sender)

                sku = self.find_sku(purchase)
                # create Robot account for Quay.io
                with docker.QuayIOAccount(purchase.subscription) as account:
                    account.create()
                    utils.configure_product_access(account, sku)

                # ask them to subscribe to newsletter
                mailchimp.subscribe(purchase.sender)

            if self.action_is_recurring_billing(purchase):
                # create an account in case it has expired or details have changed
                self.create_user_account(purchase.sender)

                # WARNING: this relies on the fact that vendor specific
                # classes will override this method in order to find the exact
                # tenant for each customer
                tenant = self.find_paid_tenant(purchase).first()
                if tenant:
                    tenant.paid_until = utils.calculate_paid_until(
                        purchase.payload["marketplace_purchase"],
                        purchase.effective_date,
                    )
                    tenant.save()

        return self.vendor_response(purchase)


@method_decorator(csrf_exempt, name="dispatch")
class PurchaseHook(GenericPurchaseNotificationView):
    """
    Handles `marketplace_purchase` web hook as described at:
    https://developer.github.com/marketplace/listing-on-github-marketplace/configuring-the-github-marketplace-webhook/

    Hook must be configured to receive JSON payload! See:
    https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/github-marketplace-webhook-events/
    """

    purchase_vendor = "github"

    def action_is_activated(self, purchase):
        return (
            purchase.action == "purchased"
            and purchase.payload["marketplace_purchase"]["plan"][
                "monthly_price_in_cents"
            ]
            > 0
        )

    def action_is_recurring_billing(self, purchase):
        """
        GitHub Marketplace doesn't send web hook payloads for recurring billing!
        """
        return False

    def action_is_cancelled(self, purchase):
        return purchase.action == "cancelled"

    def find_paid_tenant(self, purchase):
        """
        On GitHub Marketplace you can't change the buyer and a single
        account may be purchasing on behalf of several organizations.
        We support 1 tenant per buyer/org combo!
        """
        tenant_organization = utils.organization_from_purchase(purchase)

        query = super().find_paid_tenant(purchase)
        return query.filter(
            Q(owner__email=purchase.sender) | Q(owner__username=purchase.sender),
            organization=tenant_organization,
        )

    def find_sku(self, purchase):
        return github_find_sku(purchase)

    def purchase_action(self, event):
        return event["action"]

    def purchase_effective_date(self, event):
        # format is 2017-10-25T00:00:00+00:00
        return datetime.strptime(event["effective_date"][:19], "%Y-%m-%dT%H:%M:%S")

    def purchase_gitops_prefix(self, event):
        # Note: works for both organizations and users
        login = event["marketplace_purchase"]["account"]["login"]

        return f"https://github.com/{login}"

    def purchase_sender(self, event):
        """
        Prefer the email of the user doing the action b/c they are probably the one who
        will be logging into Kiwi TCMS. In some case users don't want their emails disclosed
        so default to the billing email instead of returning None.
        """
        return (
            event["sender"]["email"]
            or event["marketplace_purchase"]["account"]["organization_billing_email"]
        )

    def purchase_should_have_tenant(self, event):
        """
        https://github.com/marketplace/kiwi-tcms/ doesn't list the full range of products.
        The products currently available are:
        - FREE Demo
        - Self Support
        - Private Tenant
        """
        return event["marketplace_purchase"]["plan"]["name"].lower() == "private tenant"

    def purchase_subscription(self, event):
        """
        The result is a string of the format:

        gh-<user-id>-<user|organization ID>

        If left == right then the sender is installing the application for themselves,
        otherwise they are purchasing on behalf of an organization!
        """
        sender_id = event["sender"]["id"]
        account_id = event["marketplace_purchase"]["account"]["id"]
        return f"gh-{sender_id}-{account_id}"

    def request_verify_signature(self, request):
        return github.verify_signature(request, settings.KIWI_GITHUB_MARKETPLACE_SECRET)

    def vendor_pre_process_request(
        self, request, payload
    ):  # pylint: disable=unused-argument
        # ping hook https://developer.github.com/webhooks/#ping-event
        if "zen" in payload:
            return HttpResponse("pong", content_type="text/plain")

        return None

    def vendor_pre_process_payload(self, payload):  # pylint: disable=unused-argument
        """
        GitHub doesn't batch events into its hooks however the workflow code
        needs to be able to iterate over the data structure!
        """
        return [payload]


class GithubCronProcessor(PurchaseHook):
    """
    Called internally with payloads which simulate recurring billing for
    GitHub Marketplace subscriptions
    """

    purchase_vendor = "github_cron"

    def request_verify_signature(self, request):
        return True

    def action_is_activated(self, purchase):
        return False

    def action_is_recurring_billing(self, purchase):
        return True


@method_decorator(csrf_exempt, name="dispatch")
class FastSpringHook(GenericPurchaseNotificationView):
    """
    Handles web hook events as described at:
    https://docs.fastspring.com/integrating-with-fastspring/webhooks
    """

    purchase_vendor = "fastspring"

    def action_is_activated(self, purchase):
        return purchase.payload["type"] == "subscription.activated"

    def action_is_cancelled(self, purchase):
        return purchase.payload["type"] == "subscription.deactivated"

    def action_is_recurring_billing(self, purchase):
        return purchase.payload["type"] == "subscription.charge.completed"

    def find_paid_tenant(self, purchase):
        """
        On FastSpring buyers can change their email addresses over time and
        we may end-up in a situation where the email address on a Purchase does
        not match an existing tenant owner. That's why we look into historical
        records and try to find all unique addresses associated with a Customer.

        Also try matching the current ``purchase.sender`` against
        ``Tenant.extra_emails`` for the situation where ``Tenant.owner`` is no
        longer the one who pays the subscription.

        WARNING: Tenant.organization doesn't matter for FastSpring purchases!
        """
        all_senders = Purchase.objects.filter(
            action="purchased",
            vendor=self.purchase_vendor,
            subscription=purchase.subscription,
        ).values_list("sender", flat=True)

        query = super().find_paid_tenant(purchase)
        return query.filter(
            Q(owner__email__in=all_senders)
            | Q(owner__username__in=all_senders)
            | Q(extra_emails__icontains=purchase.sender),
        )

    def find_sku(self, purchase):
        return fastspring.find_sku(purchase)

    def purchase_action(self, event):
        # Adjust to GitHub's format b/c we have legacy records in the DB
        if event["type"] in ["subscription.activated", "subscription.charge.completed"]:
            return "purchased"

        if event["type"] == "subscription.deactivated":
            return "cancelled"

        return event["type"]

    def purchase_effective_date(self, event):
        # timestamp is in milliseconds
        return datetime.fromtimestamp(event["created"] / 1000)

    def purchase_sender(self, event):
        return event["data"]["account"]["contact"]["email"]

    def purchase_should_have_tenant(self, event):
        return "x-tenant" in self.find_sku(event)

    def purchase_subscription(self, event):
        subscription = None

        data = event["data"]
        if "subscription" in data:
            subscription = data["subscription"]
            if isinstance(subscription, dict):
                subscription = subscription["id"]

        return f"fs-{subscription}"

    def request_verify_signature(self, request):
        return utils.verify_hmac(request)

    def find_billing_cycle_interval(self, event):
        interval = ""
        event_as_string = json.dumps(event)

        if (
            "product" in event["data"]
            and "pricing" in event["data"]["product"]
            and "interval" in event["data"]["product"]["pricing"]
        ):
            interval = event["data"]["product"]["pricing"]["interval"]
        elif (
            "subscription" in event["data"]
            and "intervalUnit" in event["data"]["subscription"]
        ):
            interval = event["data"]["subscription"]["intervalUnit"]
        elif "intervalUnit" in event["data"]:
            interval = event["data"]["intervalUnit"]
        elif (
            "instructions" in event["data"]
            and event["data"]["instructions"]
            and "intervalUnit" in event["data"]["instructions"][0]
        ):
            interval = event["data"]["instructions"][0]["intervalUnit"]
        elif (
            "items" in event["data"]
            and event["data"]["items"]
            and "subscription" in event["data"]["items"][0]
            and "intervalUnit" in event["data"]["items"][0]["subscription"]
        ):
            interval = event["data"]["items"][0]["subscription"]["intervalUnit"]
        elif "additional-services-for-kiwi-tcms" in event_as_string:
            return "one-time"
        elif "subscription" not in event_as_string:
            return "not-a-subscription"
        else:
            return "unrecognized"

        if interval == "month":
            return "monthly"

        if interval == "year":
            return "yearly"

        raise RuntimeError(f"Unsupported billing cycle: '{interval}'")

    def vendor_pre_process_payload(self, payload):  # pylint: disable=unused-argument
        """
        Multiple webhooks might be combined in a single payload. We need to adjust
        the internal data to match the calculations for subscription renewals which are
        based on the GitHub Marketplace data structure!
        """
        for event in payload["events"]:
            sub_total_in_payout_currency = 0
            if "subtotalInPayoutCurrency" in event["data"]:
                sub_total_in_payout_currency = event["data"]["subtotalInPayoutCurrency"]
            elif "subtotalInPayoutCurrency" in event["data"]["subscription"]:
                sub_total_in_payout_currency = event["data"]["subscription"][
                    "subtotalInPayoutCurrency"
                ]
            elif "subtotalInPayoutCurrency" in event["data"]["order"]:
                sub_total_in_payout_currency = event["data"]["order"][
                    "subtotalInPayoutCurrency"
                ]
            else:
                raise RuntimeError(
                    "subtotalInPayoutCurrency not found in FastSpring data"
                )

            event["marketplace_purchase"] = {
                "billing_cycle": self.find_billing_cycle_interval(event),
                "plan": {
                    "monthly_price_in_cents": sub_total_in_payout_currency * 100,
                },
                "account": {
                    "type": "User",  # no organization support for FastSpring
                },
            }

        return payload["events"]


@method_decorator(csrf_exempt, name="dispatch")
class ProcessManualPurchase(GenericPurchaseNotificationView):
    """
    Handles manual purchases confirmed via the Admin panel.
    """

    purchase_vendor = "manual_purchase"

    def action_is_activated(self, purchase):
        return purchase.payload["action"] == "purchased"

    def action_is_cancelled(self, purchase):
        return purchase.payload["action"] == "cancelled"

    def action_is_recurring_billing(self, purchase):
        """
        For now we don't have a different action value that differentiates
        rebilling of manually confirmed purchases, see ManualPurchaseAdmin.save_model().
        """
        return purchase.payload["action"] == "purchased"

    def find_paid_tenant(self, purchase):
        """
        Warning: b/c we don't have a good notion of recurring payments here
        I'm not sure how to search for existing tenants from a previous purchase!

        FIX THIS ONCE WE GET THERE!
        """
        all_senders = [
            purchase.payload["data"]["billing_email"],
            purchase.payload["data"]["technical_email"],
        ]

        query = super().find_paid_tenant(purchase)
        return query.filter(
            Q(owner__email__in=all_senders) | Q(owner__username__in=all_senders),
        )

    def find_sku(self, purchase):
        # this method is also called from purchase_should_have_tenant() which
        # only passes event JSON b/c the Purchase object hasn't been created yet
        event = purchase
        if isinstance(purchase, Purchase):
            event = purchase.payload
        assert isinstance(event, dict)

        return event["data"]["sku"]

    def purchase_action(self, event):
        return event["action"]

    def purchase_effective_date(self, event):
        # format is .isoformat() which Django is able to understand natively
        return event["effective_date"]

    def purchase_sender(self, event):
        return event["data"]["technical_email"]

    def purchase_should_have_tenant(self, event):
        return "x-tenant" in self.find_sku(event)

    def purchase_subscription(self, event):
        invoice = event["data"]["invoice"]
        return f"man-{invoice}"

    def request_verify_signature(self, request):
        """
        The `.purchase_payload` attribute is set in ManualPurchaseAdmin.response_add().

        WARNING: don't rely on headers which could be set from the outside.
        """
        payload_from_request = json.loads(request.body.decode("utf-8"))
        return request.purchase_payload == payload_from_request

    def vendor_response(self, purchase):
        """
        Send a fulfillment email to the billing & technical accounts informing
        them about their new subscription and then redirect to the Admin page!
        """
        if self.action_is_activated(purchase):
            # converts via a set to filter out duplicate addresses
            recipients = list(
                set(
                    [
                        purchase.payload["data"]["billing_email"],
                        purchase.payload["data"]["technical_email"],
                    ]
                )
            )
            # sort the list so the order is the same within tests
            recipients.sort()

            mailto(
                template_name="email/manual_subscription_notification.txt",
                recipients=recipients,
                subject=str(_("Kiwi TCMS subscription notification")),
                context={},
            )

        return HttpResponseRedirect(
            reverse("admin:tcms_github_marketplace_purchase_changelist")
        )


@method_decorator(login_required, name="dispatch")
class Install(View):
    """
    Handles application "installation", see:
    https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/handling-new-purchases-and-free-trials/

    1) User makes an initial purchase and GitHub sends
       `marketplace_purchase` hook which is handled in PurchaseHook view
       and the payload is stored in DB.
    2) GitHub will then redirect to the Installation URL which is this
       view.
    3) Because we are an OAuth app begin the authorization flow as soon as
       GitHub redirects the customer to the Installation URL.

       NOTE: this is achieved by @login_required and configuring the
       Installation URL (in Marketplace listing) to go through the
       Python-Social-Auth pipeline which we already have installed in the
       main application!

    4) Provision resources for customer - actually handled below
    """

    http_method_names = ["get", "head", "options"]

    def get(self, request, *args, **kwargs):  # pylint: disable=unused-argument
        """
        Read marketplace_purchase data for the currently logged in
        user and figure out how to provision resources.
        """
        # we take the most recent purchase event for this user
        purchase = (
            Purchase.objects.filter(sender=request.user.email, should_have_tenant=True)
            .order_by("-received_on")
            .first()
        )

        # if user somehow visits this URL without having purchased the app
        if not purchase:
            return HttpResponseRedirect("/")

        if purchase.action == "purchased":
            plan_price = purchase.payload["marketplace_purchase"]["plan"][
                "monthly_price_in_cents"
            ]

            # Free Marketplace plans have nothing to install so they
            # just redirect to the Public tenant
            if plan_price == 0:
                return HttpResponseRedirect("/")

            return HttpResponseRedirect(reverse("github_marketplace_create_tenant"))

        raise NotImplementedError(
            f'Unsupported GitHub Marketplace action: "{purchase.action}"'
        )


@method_decorator(login_required, name="dispatch")
class CreateTenant(NewTenantView):
    purchase = None
    organization = None

    def dispatch(self, request, *args, **kwargs):
        """
        Jump over NewTenantView class b/c it requires the tcms_tenants.add_tenant
        permission while on Marketplace we allow everyone who had paid their subscription
        to create tenants!
        """
        # we take the most recent purchase event for this user
        # where they purchase a paid plan
        # pylint: disable=attribute-defined-outside-init
        if not self.purchase:
            self.purchase = (
                Purchase.objects.filter(
                    sender=request.user.email,
                    action="purchased",
                    should_have_tenant=True,
                    payload__marketplace_purchase__plan__monthly_price_in_cents__gt=0,
                )
                .order_by("-received_on")
                .first()
            )
        if not self.organization:
            self.organization = utils.organization_from_purchase(self.purchase)

        return super(NewTenantView, self).dispatch(  # pylint: disable=bad-super-call
            request, *args, **kwargs
        )

    def check(self, request):
        """
        Doesn't allow user to create more than 1 tenant!
        If they have a tenant already then we redirect to it!
        """
        # if user somehow visits this URL without having purchased the app
        if not self.purchase and not request.user.is_superuser:
            return HttpResponseRedirect("/")

        tenant = Tenant.objects.filter(
            owner=request.user,
            organization=self.organization,
        ).first()

        # only 1 tenant per owner+organization combo allowed
        if tenant and not request.user.is_superuser:
            return HttpResponseRedirect(
                tcms_tenants_utils.tenant_url(request, tenant.schema_name)
            )

        return None

    def get(self, request, *args, **kwargs):
        return self.check(request) or super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.check(request) or super().post(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.purchase:
            paid_until = utils.calculate_paid_until(
                self.purchase.payload["marketplace_purchase"],
                self.purchase.effective_date,
            )
            kwargs["initial"]["paid_until"] = paid_until

        kwargs["initial"]["organization"] = self.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_action_url"] = reverse("github_marketplace_create_tenant")
        return context


@method_decorator(login_required, name="dispatch")
class ViewSubscriptionPlan(UpdateView):
    """
    This view shows information about current subscription plan and allows
    user to edit Purchase.gitops_prefix field if not set!
    """

    model = Purchase
    form_class = forms.UpdateGitopsPrefixForm
    success_url = reverse_lazy("github_marketplace_plans")
    template_name = "tcms_github_marketplace/subscription.html"

    def form_valid(self, form):
        # clear gitops_prefix cache!
        cache.clear()

        return super().form_valid(form)

    def get_queryset(self):
        """
        All purchases for the currently logged-in user
        """
        return Purchase.objects.filter(
            sender=self.request.user.email,
        ).order_by("-received_on")

    def get_object(self, queryset=None):
        """
        Always returns the latest purchase for the current user
        which has the subscription field set! Note that some events,
        e.g. order.canceled may have this field set to None
        """
        return self.get_queryset().exclude(subscription=None).first()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        cancel_url = None
        quay_io_account = None

        subscription_price = "-"
        subscription_period = "-"

        if self.object is not None:
            subscription_price = "0"
            quay_io_account = docker.QuayIOAccount(self.object.subscription)

            if self.object.vendor.lower() == "github":
                cancel_url = "https://github.com/settings/billing"

            if self.object.vendor.lower() == "fastspring":
                cancel_url = self.object.payload["data"]["account"]["url"]

            purchase_data = self.object.payload["marketplace_purchase"]
            if purchase_data["billing_cycle"] == "monthly":
                subscription_price = (
                    purchase_data["plan"]["monthly_price_in_cents"] // 100
                )
                subscription_period = _("mo")
            elif purchase_data["billing_cycle"] == "yearly":
                subscription_price = (
                    purchase_data["plan"]["yearly_price_in_cents"] // 100
                )
                subscription_period = _("yr")

            subscription_price = int(subscription_price)

        context.update(
            {
                "access_tenants": self.request.user.tenant_set.all(),
                "own_tenants": Tenant.objects.filter(owner=self.request.user),
                "purchases": self.get_queryset(),
                "subscription_price": subscription_price,
                "subscription_period": subscription_period,
                "cancel_url": cancel_url,
                "quay_io_account": quay_io_account,
            }
        )

        return context
