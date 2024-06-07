# Copyright (c) 2019-2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import json

from django import forms
from django import http
from django.urls import reverse
from django.utils import timezone
from django.contrib import admin
from django.http import HttpResponseForbidden, HttpResponseRedirect

from tcms_github_marketplace.models import ManualPurchase, Purchase


class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "vendor",
        "monthly_price",
        "yearly_price",
        "action",
        "sender",
        "subscription",
        "effective_date",
        "received_on",
        "should_have_tenant",
        "should_have_support",
        "gitops_prefix",
    )
    list_filter = ("action", "vendor", "sender")
    search_fields = ("action", "vendor", "sender", "subscription", "gitops_prefix")
    ordering = ["-pk"]

    def monthly_price(self, purchase):  # pylint: disable=no-self-use
        return int(
            purchase.payload["marketplace_purchase"]["plan"].get(
                "monthly_price_in_cents", 0
            )
            / 100
        )

    monthly_price.short_description = "$/mo"

    def yearly_price(self, purchase):  # pylint: disable=no-self-use
        return int(
            purchase.payload["marketplace_purchase"]["plan"].get(
                "yearly_price_in_cents", 0
            )
            / 100
        )

    yearly_price.short_description = "$/yr"

    def add_view(self, request, form_url="", extra_context=None):
        return HttpResponseRedirect(
            reverse("admin:tcms_github_marketplace_purchase_changelist")
        )

    @admin.options.csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        if request.user.is_superuser:
            return super().changelist_view(request, extra_context)

        return HttpResponseForbidden("Unauthorized")

    @admin.options.csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        return HttpResponseRedirect(
            reverse("admin:tcms_github_marketplace_purchase_changelist")
        )


# pylint: disable=form-field-label-used, form-field-help-text-used
class ManualPurchaseForm(forms.ModelForm):
    invoice = forms.CharField(
        required=True,
        label="Invoice No.",
        help_text="NUM-YYYY-MM-DD. Will be used as the Subscription ID",
    )
    price = forms.IntegerField(
        required=True, label="Price in USD", help_text="Per billing cycle!"
    )
    billing_cycle = forms.ChoiceField(
        required=True,
        choices=(
            ("", "-----"),
            ("yearly", "Yearly"),
            ("monthly", "Monthly"),
        ),
    )
    customer_name = forms.CharField(required=True)
    address = forms.CharField(required=True)
    billing_email = forms.EmailField(
        required=True,
        help_text="will receive product renewal information",
    )
    technical_email = forms.EmailField(
        required=True,
        help_text="will receive product access and will be subscribed to newsletter",
    )
    sku = forms.CharField(
        required=True,
        max_length=256,
        label="SKU",
        help_text="e.g: x-tenant+version+enterprise",
    )

    class Meta:
        model = ManualPurchase
        fields = "__all__"


class ManualPurchaseAdmin(admin.ModelAdmin):
    form = ManualPurchaseForm

    @staticmethod
    def calculate_price_in_cents(form):
        billing_cycle = form.cleaned_data["billing_cycle"]
        monthly_price = 0
        yearly_price = 0

        if billing_cycle == "monthly":
            monthly_price = form.cleaned_data["price"] * 100
            yearly_price = monthly_price * 12
        elif billing_cycle == "yearly":
            yearly_price = form.cleaned_data["price"] * 100
            monthly_price = int(yearly_price / 12)
        else:
            raise RuntimeError(f"Unrecognized billong cycle '{billing_cycle}'")

        return (monthly_price, yearly_price)

    def save_model(self, request, obj, form, change):
        monthly_price, yearly_price = self.calculate_price_in_cents(form)

        # WARNING that payload needs to be a list of events!
        request.purchase_payload = [
            {
                "action": "purchased",
                "effective_date": timezone.now().isoformat(),
                "data": form.cleaned_data,
                "marketplace_purchase": {
                    "account": {
                        "type": "User",
                    },
                    "billing_cycle": form.cleaned_data["billing_cycle"],
                    "plan": {
                        "monthly_price_in_cents": monthly_price,
                        "yearly_price_in_cents": yearly_price,
                    },
                },
            }
        ]

    def response_add(
        self, request, obj, post_url_continue=None
    ):  # pylint: disable=protected-access
        """
        Gets called after self.save_model() and determines the response
        after a new object has been added. Must return an HttpResponse instance!

        Builds an internal POST request containing JSON data about the subscription
        and routes it internally to the corresponding view!
        """
        post_body = json.dumps(request.purchase_payload).encode("utf-8")
        request.META["REQUEST_METHOD"] = "POST"
        request.META["CONTENT_LENGTH"] = len(post_body)
        request.META["CONTENT_TYPE"] = "application/json"

        new_request = request.__class__(request.META)
        new_request.purchase_payload = request.purchase_payload
        new_request._body = post_body
        new_request._post = http.QueryDict(post_body, encoding=new_request._encoding)

        from .views import (  # pylint: disable=import-outside-toplevel
            ProcessManualPurchase,
        )

        return ProcessManualPurchase.as_view()(new_request)


admin.site.register(ManualPurchase, ManualPurchaseAdmin)
admin.site.register(Purchase, PurchaseAdmin)
