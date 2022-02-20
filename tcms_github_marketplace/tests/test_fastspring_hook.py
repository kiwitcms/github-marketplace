# Copyright (c) 2022 Alexander Todorov <atodorov@MrSenko.com>

# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt
# pylint: disable=too-many-ancestors
import json
import hmac
import hashlib

from unittest.mock import patch
from base64 import b64encode

from django.urls import reverse
from django.conf import settings
from django.contrib.auth import get_user_model

from social_django.models import UserSocialAuth

import tcms_tenants

from tcms_github_marketplace import docker
from tcms_github_marketplace import utils
from tcms_github_marketplace.models import Purchase


class FastSpringHookTestCase(tcms_tenants.tests.LoggedInTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.purchase_hook_url = reverse("fastspring")
        # simulate existing GitHub login
        UserSocialAuth.objects.create(
            user=cls.tester,
            provider="github",
            uid="123456",
            extra_data={"access_token": "TEST-ME", "token_type": "bearer"},
        )

        cls.gh_revoke_url = (
            f"/applications/{settings.SOCIAL_AUTH_GITHUB_KEY}/tokens/TEST-ME"
        )

    @staticmethod
    def calculate_signature(str_payload):
        payload = json.dumps(json.loads(str_payload)).encode()
        payload_signature = hmac.new(
            settings.KIWI_FASTSPRING_SECRET, msg=payload, digestmod=hashlib.sha256
        ).digest()
        # turn binary string into str !!!
        return b64encode(payload_signature).decode()

    def test_subscription_deactivated(self):
        payload = """
{
    "events": [
        {
          "id": "Gl_Xo3kYT2SWQtogF3xXJQ",
          "data": {
            "id": "TUmTFphXT6aRsJ_7hIlW1g",
            "end": null,
            "sku": null,
            "live": true,
            "next": 1644105600000,
            "adhoc": false,
            "begin": 1588723200000,
            "price": 32,
            "quote": null,
            "state": "deactivated",
            "active": false,
            "account": {
              "id": "6Otj",
              "account": "6Otj",
              "address": {
                "city": "Sofia",
                "region": "",
                "company": "BG",
                "postal code": "3",
                "region custom": null,
                "address line 1": null,
                "address line 2": null
              },
              "contact": {
                "last": "%s",
                "email": "%s",
                "first": "%s",
                "phone": "55555",
                "company": "Kiwi TCMS",
                "subscribed": true
              },
              "country": "BG",
              "language": "en"
            },
            "changed": 1644135296221,
            "display": "Kiwi TCMS Private Tenant",
            "periods": null,
            "product": {
              "image": "https://d8y8nchqlnmka.cloudfront.net/XAeq54smTQ8/gahPnpQiREI/square-with-name.png",
              "format": "digital",
              "parent": null,
              "display": {
                "en": "Kiwi TCMS Private Tenant"
              },
              "pricing": {
                "price": {
                  "USD": 50
                },
                "renew": "auto",
                "interval": "month",
                "cancellation": {
                  "interval": "week",
                  "intervalLength": 1
                },
                "intervalCount": null,
                "intervalLength": 1,
                "quantityDefault": 1,
                "quantityBehavior": "allow",
                "dateLimitsEnabled": false,
                "overdueNotification": {
                  "amount": 4,
                  "enabled": true,
                  "interval": "week",
                  "intervalLength": 1
                },
                "reminderNotification": {
                  "enabled": true,
                  "interval": "week",
                  "intervalLength": 1
                }
              },
              "product": "kiwitcms-private-tenant",
              "taxcode": "SW054000",
              "description": {
                "summary": {
                  "en": "Unlimited users."
                }
              },
              "fulfillments": {
                "kiwitcms-private-tenant_email_0": {
                  "name": "Email (#{orderItem.display} Delivery ...)",
                  "fulfillment": "kiwitcms-private-tenant_email_0",
                  "applicability": "NON_REBILL_ONLY"
                }
              },
              "taxcodeDescription": "Cloud Services - SaaS - Service Agreement",
              "productAppReference": "7yDTCEDoSt6S44eWtgVc_g"
            },
            "currency": "USD",
            "discount": 0,
            "endValue": null,
            "quantity": 1,
            "sequence": 21,
            "subtotal": 32,
            "autoRenew": true,
            "nextValue": 1644105600000,
            "beginValue": 1588723200000,
            "endDisplay": null,
            "nextDisplay": "2/6/22",
            "beginDisplay": "5/6/20",
            "canceledDate": 1643587200000,
            "changedValue": 1644135296221,
            "endInSeconds": null,
            "fulfillments": {},
            "instructions": [
              {
                "type": "regular",
                "price": 32,
                "total": 32,
                "product": "kiwitcms-private-tenant",
                "unitPrice": 32,
                "priceTotal": 32,
                "intervalUnit": "month",
                "priceDisplay": "$32.00",
                "totalDisplay": "$32.00",
                "unitDiscount": 0,
                "discountTotal": 0,
                "periodEndDate": null,
                "intervalLength": 1,
                "discountPercent": 0,
                "periodStartDate": null,
                "unitPriceDisplay": "$32.00",
                "priceTotalDisplay": "$32.00",
                "periodEndDateValue": null,
                "unitDiscountDisplay": "$0.00",
                "discountPercentValue": 0,
                "discountTotalDisplay": "$0.00",
                "periodEndDateDisplay": null,
                "periodStartDateValue": null,
                "priceInPayoutCurrency": 32,
                "totalInPayoutCurrency": 32,
                "periodEndDateInSeconds": null,
                "periodStartDateDisplay": null,
                "periodStartDateInSeconds": null,
                "unitPriceInPayoutCurrency": 32,
                "priceTotalInPayoutCurrency": 32,
                "priceInPayoutCurrencyDisplay": "$32.00",
                "totalInPayoutCurrencyDisplay": "$32.00",
                "unitDiscountInPayoutCurrency": 0,
                "discountTotalInPayoutCurrency": 0,
                "unitPriceInPayoutCurrencyDisplay": "$32.00",
                "priceTotalInPayoutCurrencyDisplay": "$32.00",
                "unitDiscountInPayoutCurrencyDisplay": "$0.00",
                "discountTotalInPayoutCurrencyDisplay": "$0.00"
              }
            ],
            "intervalUnit": "month",
            "priceDisplay": "$32.00",
            "subscription": "TUmTFphXT6aRsJ_7hIlW1g",
            "nextInSeconds": 1644105600,
            "beginInSeconds": 1588723200,
            "changedDisplay": "2/6/22",
            "intervalLength": 1,
            "paymentOverdue": {
              "sent": 0,
              "total": 4,
              "intervalUnit": "week",
              "intervalLength": 1
            },
            "discountDisplay": "$0.00",
            "paymentReminder": {
              "intervalUnit": "week",
              "intervalLength": 1
            },
            "subtotalDisplay": "$32.00",
            "changedInSeconds": 1644135296,
            "deactivationDate": 1644105600000,
            "remainingPeriods": null,
            "canceledDateValue": 1643587200000,
            "canceledDateDisplay": "1/31/22",
            "cancellationSetting": {
              "cancellation": "AFTER_LAST_NOTIFICATION",
              "intervalUnit": "week",
              "intervalLength": 1
            },
            "canceledDateInSeconds": 1643587200,
            "deactivationDateValue": 1644105600000,
            "priceInPayoutCurrency": 32,
            "deactivationDateDisplay": "2/6/22",
            "discountInPayoutCurrency": 0,
            "subtotalInPayoutCurrency": 32,
            "deactivationDateInSeconds": 1644105600,
            "priceInPayoutCurrencyDisplay": "$32.00",
            "discountInPayoutCurrencyDisplay": "$0.00",
            "subtotalInPayoutCurrencyDisplay": "$32.00"
          },
          "live": true,
          "type": "subscription.deactivated",
          "created": 1644135296331,
          "processed": false,
          "marketplace_purchase": {
            "plan": {
              "monthly_price_in_cents": 3200
            },
            "account": {
              "type": "User"
            },
            "billing_cycle": "monthly"
          }
        }
    ]
}
""".strip() % (
            self.tester.last_name,
            self.tester.email,
            self.tester.first_name,
        )

        signature = self.calculate_signature(payload)

        with patch.object(
            utils.Requester, "requestJsonAndCheck", return_value=({}, None)
        ) as gh_api, patch.object(
            docker.QuayIOAccount, "delete", return_value=""
        ) as quay_io_api:
            response = self.client.post(
                self.purchase_hook_url,
                json.loads(payload),
                content_type="application/json",
                HTTP_X_FS_SIGNATURE=signature,
            )
            self.assertContains(response, "cancelled")
            gh_api.assert_called_with("DELETE", self.gh_revoke_url)
            quay_io_api.assert_called_once()

        # verify user is not present anymore
        self.assertFalse(
            get_user_model().objects.filter(username=self.tester.username).exists()
        )

    def test_subscription_activated(self):
        payload = """
{
    "events": [
        {
          "id": "9cMkAyvIT6aha_KwS0M6aw",
          "data": {
            "id": "_fmtng11QUyLno5-5aVB-w",
            "end": null,
            "sku": "x-tenant+version",
            "live": true,
            "next": 1646179200000,
            "adhoc": false,
            "begin": 1643760000000,
            "price": 56,
            "quote": null,
            "state": "active",
            "active": true,
            "account": {
              "id": "vvvv",
              "url": "https://mrsenko.onfastspring.com/account",
              "lookup": {
                "global": "SSSSS"
              },
              "account": "vvvv",
              "address": {
                "city": null,
                "region": null,
                "company": "BG",
                "postal code": null,
                "region custom": null,
                "address line 1": null,
                "address line 2": null
              },
              "contact": {
                "first": "%s",
                "last": "%s",
                "email": "%s",
                "phone": "000",
                "company": "Kiwi TCMS",
                "subscribed": true
              },
              "country": "BG",
              "language": "en"
            },
            "changed": 1643836213623,
            "display": "Kiwi TCMS Private Tenant",
            "periods": null,
            "product": {
              "sku": "version",
              "image": "https://d8y8nchqlnmka.cloudfront.net/XAeq54smTQ8/gahPnpQiREI/square-with-name.png",
              "format": "digital",
              "parent": null,
              "display": {
                "en": "Kiwi TCMS Private Tenant"
              },
              "pricing": {
                "price": {
                  "USD": 50
                },
                "renew": "auto",
                "interval": "month",
                "cancellation": {
                  "interval": "week",
                  "intervalLength": 1
                },
                "intervalCount": null,
                "intervalLength": 1,
                "quantityDefault": 1,
                "quantityBehavior": "allow",
                "dateLimitsEnabled": false,
                "overdueNotification": {
                  "amount": 4,
                  "enabled": true,
                  "interval": "week",
                  "intervalLength": 1
                },
                "reminderNotification": {
                  "enabled": true,
                  "interval": "week",
                  "intervalLength": 1
                }
              },
              "product": "kiwitcms-private-tenant",
              "taxcode": "SW054000",
              "description": {
                "summary": {
                  "en": "Unlimited users."
                }
              },
              "fulfillments": {
                "kiwitcms-private-tenant_email_0": {
                  "name": "Email (#{orderItem.display} Delivery ...)",
                  "fulfillment": "kiwitcms-private-tenant_email_0",
                  "applicability": "NON_REBILL_ONLY"
                }
              },
              "taxcodeDescription": "Cloud Services - SaaS - Service Agreement",
              "productAppReference": "7yDTCEDoSt6S44eWtgVc_g"
            },
            "currency": "EUR",
            "discount": 0,
            "endValue": null,
            "quantity": 1,
            "sequence": 1,
            "subtotal": 46.67,
            "autoRenew": true,
            "nextValue": 1646179200000,
            "beginValue": 1643760000000,
            "endDisplay": null,
            "nextDisplay": "3/2/22",
            "beginDisplay": "2/2/22",
            "canceledDate": null,
            "changedValue": 1643836213623,
            "endInSeconds": null,
            "fulfillments": {},
            "instructions": [
              {
                "type": "regular",
                "price": 56,
                "total": 56,
                "product": "kiwitcms-private-tenant",
                "unitPrice": 56,
                "priceTotal": 56,
                "intervalUnit": "month",
                "priceDisplay": "€56.00",
                "totalDisplay": "€56.00",
                "unitDiscount": 0,
                "discountTotal": 0,
                "periodEndDate": null,
                "intervalLength": 1,
                "discountPercent": 0,
                "periodStartDate": null,
                "unitPriceDisplay": "€56.00",
                "priceTotalDisplay": "€56.00",
                "periodEndDateValue": null,
                "unitDiscountDisplay": "€0.00",
                "discountPercentValue": 0,
                "discountTotalDisplay": "€0.00",
                "periodEndDateDisplay": null,
                "periodStartDateValue": null,
                "priceInPayoutCurrency": 60.81,
                "totalInPayoutCurrency": 60.81,
                "periodEndDateInSeconds": null,
                "periodStartDateDisplay": null,
                "periodStartDateInSeconds": null,
                "unitPriceInPayoutCurrency": 60.81,
                "priceTotalInPayoutCurrency": 60.81,
                "priceInPayoutCurrencyDisplay": "$60.81",
                "totalInPayoutCurrencyDisplay": "$60.81",
                "unitDiscountInPayoutCurrency": 0,
                "discountTotalInPayoutCurrency": 0,
                "unitPriceInPayoutCurrencyDisplay": "$60.81",
                "priceTotalInPayoutCurrencyDisplay": "$60.81",
                "unitDiscountInPayoutCurrencyDisplay": "$0.00",
                "discountTotalInPayoutCurrencyDisplay": "$0.00"
              }
            ],
            "intervalUnit": "month",
            "priceDisplay": "€56.00",
            "subscription": "_fmtng11QUyLno5-5aVB-w",
            "nextInSeconds": 1646179200,
            "beginInSeconds": 1643760000,
            "changedDisplay": "2/2/22",
            "intervalLength": 1,
            "nextChargeDate": 1646179200000,
            "paymentOverdue": {
              "sent": 0,
              "total": 4,
              "intervalUnit": "week",
              "intervalLength": 1
            },
            "discountDisplay": "€0.00",
            "nextChargeTotal": 46.67,
            "paymentReminder": {
              "intervalUnit": "week",
              "intervalLength": 1
            },
            "subtotalDisplay": "€46.67",
            "changedInSeconds": 1643836213,
            "deactivationDate": null,
            "nextChargePreTax": 46.67,
            "remainingPeriods": null,
            "taxExemptionData": "BG200",
            "canceledDateValue": null,
            "nextChargeCurrency": "EUR",
            "canceledDateDisplay": null,
            "cancellationSetting": {
              "cancellation": "AFTER_LAST_NOTIFICATION",
              "intervalUnit": "week",
              "intervalLength": 1
            },
            "nextChargeDateValue": 1646179200000,
            "nextNotificationDate": 1645574400000,
            "nextNotificationType": "PAYMENT_REMINDER",
            "canceledDateInSeconds": null,
            "deactivationDateValue": null,
            "nextChargeDateDisplay": "3/2/22",
            "priceInPayoutCurrency": 60.81,
            "nextChargeTotalDisplay": "€46.67",
            "deactivationDateDisplay": null,
            "nextChargeDateInSeconds": 1646179200,
            "nextChargePreTaxDisplay": "€46.67",
            "discountInPayoutCurrency": 0,
            "subtotalInPayoutCurrency": 50.68,
            "deactivationDateInSeconds": null,
            "nextNotificationDateValue": 1645574400000,
            "nextNotificationDateDisplay": "2/23/22",
            "priceInPayoutCurrencyDisplay": "$60.81",
            "nextNotificationDateInSeconds": 1645574400,
            "discountInPayoutCurrencyDisplay": "$0.00",
            "nextChargeTotalInPayoutCurrency": 50.68,
            "subtotalInPayoutCurrencyDisplay": "$50.68",
            "nextChargePreTaxInPayoutCurrency": 50.68,
            "nextChargeTotalInPayoutCurrencyDisplay": "$50.68",
            "nextChargePreTaxInPayoutCurrencyDisplay": "$50.68"
          },
          "live": true,
          "type": "subscription.activated",
          "created": 1643836213792,
          "processed": false,
          "marketplace_purchase": {
            "plan": {
              "monthly_price_in_cents": 5068
            },
            "account": {
              "type": "User"
            },
            "billing_cycle": "monthly"
          }
        }
    ]
}
""".strip() % (
            self.tester.first_name,
            self.tester.last_name,
            self.tester.email,
        )

        signature = self.calculate_signature(payload)

        initial_purchase_count = Purchase.objects.count()
        self.assertFalse(
            Purchase.objects.filter(
                vendor="fastspring", action="purchased", sender=self.tester.email
            ).exists()
        )

        # tmp_account calculates the actual robot name for mocking - currently not in use
        with docker.QuayIOAccount(self.tester.email) as tmp_account:
            with patch.object(
                docker.QuayIOAccount,
                "create",
                return_value={"name": tmp_account.name, "token": "secret"},
            ) as quay_io_create, patch.object(
                docker.QuayIOAccount,
                "allow_read_access",
                return_value="success",
            ) as quay_io_allow_read_access:
                response = self.client.post(
                    self.purchase_hook_url,
                    json.loads(payload),
                    content_type="application/json",
                    HTTP_X_FS_SIGNATURE=signature,
                )
                self.assertContains(response, "ok")
                quay_io_create.assert_called_once()
                quay_io_allow_read_access.assert_called_once_with("version")

        self.assertEqual(initial_purchase_count + 1, Purchase.objects.count())
        self.assertTrue(
            Purchase.objects.filter(
                vendor="fastspring",
                action="purchased",
                sender=self.tester.email,
                should_have_tenant=True,
            ).exists()
        )
