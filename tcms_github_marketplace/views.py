# Copyright (c) 2019 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

import json
from datetime import datetime, timedelta

from django.urls import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic.base import View, TemplateView
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required

from tcms_tenants.models import Tenant
from tcms_tenants.views import NewTenantView
from tcms_tenants import utils as tcms_tenants_utils

from tcms_github_marketplace import utils
from tcms_github_marketplace.models import Purchase


def calculate_paid_until(mp_purchase):
    """
        Calculates when access to paid services must be disabled
    """
    paid_until = datetime.now()
    if mp_purchase['next_billing_date'] is None:
        if mp_purchase['billing_cycle'] == 'monthly':
            paid_until += timedelta(days=31)
        elif mp_purchase['billing_cycle'] == 'yearly':
            paid_until += timedelta(days=366)
    else:
        # format is 2017-10-25T00:00:00+00:00
        paid_until = datetime.strptime(mp_purchase['next_billing_date'][:19],
                                       '%Y-%m-%dT%H:%M:%S')

    # above we give them 1 extra day and here we always end at 23:59:59
    return paid_until.replace(hour=23, minute=59, second=59)


class PurchaseHook(View):
    """
        Handles `marketplace_purchase` web hook as described at:
        https://developer.github.com/marketplace/listing-on-github-marketplace/configuring-the-github-marketplace-webhook/
    """
    http_method_names = ['post', 'head', 'options']

    def post(self, request, *args, **kwargs):
        """
            Hook must be configured to receive JSON payload!

            Save the 'purchased' event in the database, see:
            https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/github-marketplace-webhook-events/
        """
        result = utils.verify_signature(request)
        if result is not True:
            return result  # must be an HttpResponse then

        payload = json.loads(request.body.decode('utf-8'))

        # ping hook https://developer.github.com/webhooks/#ping-event
        if 'zen' in payload:
            return HttpResponse('pong', content_type='text/plain')

        # format is 2017-10-25T00:00:00+00:00
        effective_date = datetime.strptime(payload['effective_date'][:19],
                                           '%Y-%m-%dT%H:%M:%S')
        # save payload for future use
        purchase = Purchase.objects.create(
            vendor='github',
            action=payload['action'],
            sender=payload['sender']['login'],
            effective_date=effective_date,
            payload=payload,
        )

        # plan cancellations must be handled here
        if purchase.action == 'cancelled':
            return utils.cancel_plan(purchase)

        if purchase.action == 'purchased':
            # recurring billing events don't redirect to Install URL
            # they only send a web hook
            tenant = Tenant.objects.filter(
                owner__username=purchase.sender,
                paid_until__isnull=False,
            ).first()
            if tenant:
                tenant.paid_until = calculate_paid_until(purchase.payload['marketplace_purchase'])
                tenant.save()

        return HttpResponse('ok', content_type='text/plain')


@method_decorator(login_required, name='dispatch')
class Install(View):
    """
        Handles application "installation", see:
        https://developer.github.com/marketplace/integrating-with-the-github-marketplace-api/handling-new-purchases-and-free-trials/

        1) User makes an initial purchase and GitHub sends marketplace_purchase hook
           which is handled in PurchaseHook view and the payload is stored in DB.
        2) GitHub will then redirect to the Installation URL which is this view.
        3) Because we are an OAuth app begin the authorization flow as soon as
           GitHub redirects the customer to the Installation URL.

           NOTE: this is achieved by @login_required and configuring the
           Installation URL (in Marketplace listing) to go through the
           Python-Social-Auth pipeline which we already have installed in the
           main application!

        4) Provision resources for customer - actually handled by the code below
    """
    http_method_names = ['get', 'head', 'options']

    def get(self, request, *args, **kwargs):
        """
            Read marketplace_purchase data for the currently logged in
            user and figure out how to provision resources.
        """
        # we take the most recent purchase event for this user
        purchase = Purchase.objects.filter(
            sender=request.user.username
        ).order_by('-received_on').first()

        # if user somehow visits this URL without having purchased the app
        if not purchase:
            return HttpResponseRedirect('/')

        if purchase.action == 'purchased':
            plan_price = purchase.payload['marketplace_purchase']['plan']['monthly_price_in_cents']

            # Free Marketplace plans have nothing to install so they
            # just redirect to the Public tenant
            if plan_price == 0:
                return HttpResponseRedirect('/')

            return HttpResponseRedirect(reverse('github_marketplace_create_tenant'))

        raise NotImplementedError(
            'Unsupported GitHub Marketplace action: "%s"' %
            purchase.action)


@method_decorator(login_required, name='dispatch')
class CreateTenant(NewTenantView):
    def get(self, request, *args, **kwargs):
        """
            Doesn't allow user to create more than 1 tenant!
            If they have a tenant already then we redirect to it!
        """
        # we take the most recent purchase event for this user
        purchase = Purchase.objects.filter(
            sender=self.request.user.username,
            action='purchased',
        ).order_by('-received_on').first()

        # if user somehow visits this URL without having purchased the app
        if not purchase:
            return HttpResponseRedirect('/')

        tenant = Tenant.objects.filter(owner=request.user).first()
        # only 1 tenant per owner allowed
        if tenant and not request.user.is_superuser:
            return HttpResponseRedirect(tcms_tenants_utils.tenant_url(request, tenant.schema_name))

        # no tenant owned by the current user then allow them to create one
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
            This view is the same as tcms_tenants.views.NewTenantView
            but we override some of the hidden fields on the form.
        """
        # we take the most recent purchase event for this user
        purchase = Purchase.objects.filter(
            sender=self.request.user.username,
            action='purchased',
        ).order_by('-received_on').first()
        paid_until = calculate_paid_until(purchase.payload['marketplace_purchase'])

        context = super().get_context_data(**kwargs)
        context['form'] = context['form'].__class__(
            initial={
                'on_trial': False,
                'paid_until': paid_until,
            }
        )
        context['form_action_url'] = reverse('github_marketplace_create_tenant')
        return context


@method_decorator(login_required, name='dispatch')
class ViewSubscriptionPlan(TemplateView):
    """
        This view shows information about current subscription plan.
    """
    template_name = 'tcms_github_marketplace/subscription.html'

    def get_context_data(self, **kwargs):
        own_tenants = Tenant.objects.filter(owner=self.request.user)
        purchases = Purchase.objects.filter(
            sender=self.request.user.username,
        ).order_by('-received_on')

        mp_purchase = purchases.first()

        if mp_purchase is not None:
            mp_purchase = mp_purchase.payload['marketplace_purchase']
            if mp_purchase['billing_cycle'] == 'monthly':
                subscription_price = mp_purchase['plan']['monthly_price_in_cents'] // 100
                subscription_period = _('mo')
            elif mp_purchase['billing_cycle'] == 'yearly':
                subscription_price = mp_purchase['plan']['yearly_price_in_cents'] // 100
                subscription_period = _('yr')
        else:
            subscription_price = '-'
            subscription_period = '-'

        context = {
            'access_tenants': self.request.user.tenant_set.all(),
            'own_tenants': own_tenants,
            'purchases': purchases,
            'subscription_price': subscription_price,
            'subscription_period': subscription_period,
        }

        return context
