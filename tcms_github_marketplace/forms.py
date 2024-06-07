# Copyright (c) 2024 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import github

from django import forms
from django.conf import settings

from tcms.utils.github import repo_id as github_repo_id
from tcms_github_marketplace import fastspring
from tcms_github_marketplace import models


def get_github_user(prefix):
    repo_id = github_repo_id(prefix)
    username = repo_id.split("/")[0]

    gh = github.Github(
        auth=github.Auth.Token(
            settings.KIWI_GITHUB_PAT_FOR_CHECKING_ORGS_AND_USERNAMES,
        )
    )

    return gh.get_user(username)


def validate_prefix_for_fastspring_subscriptions(prefix, purchase):
    sku = fastspring.find_sku(purchase)
    if not sku:
        raise forms.ValidationError("SKU not found")

    # Enterprise subscribers can configure whatever prefix they want,
    # e.g. GitHub Enterprise, on-premise GitLab, SaaS, etc
    if "enterprise" in sku:
        if prefix.strip("/") == "https://github.com":
            raise forms.ValidationError("Bare https://github.com prefix not allowed")

        return

    # From here on it must be a a Private Tenant or Self-Hosted subscription.
    # They can only configure repositories hosted on GitHub.com
    if "https://github.com" not in prefix:
        raise forms.ValidationError("Only https://github.com/ prefix allowed")

    try:
        user = get_github_user(prefix)
    except github.UnknownObjectException as exc:
        raise forms.ValidationError("User or Organization not found") from exc
    except github.GithubException as exc:
        raise forms.ValidationError("API request to GitHub failed") from exc

    # Private Tenant subscribers can use both organizational & personal prefix
    if purchase.should_have_tenant:
        return

    # this leaves us with a Self-Support subscribtion
    if not purchase.should_have_tenant and user.type != "User":
        raise forms.ValidationError(
            "Self-Support subscribers cannot configure Organizational repositories"
        )

    return


def validate_prefix_against_subscription_plan(prefix, purchase):
    match purchase.vendor:
        case "github":
            # this is automated and it shouldn't be possible to change it
            raise forms.ValidationError(
                "Prefix for GitHub subscription cannot be configured manually"
            )
        case "fastspring":
            validate_prefix_for_fastspring_subscriptions(prefix, purchase)
        case _:
            raise forms.ValidationError("Unknown vendor. Contact Support")


class UpdateGitopsPrefixForm(forms.ModelForm):
    class Meta:
        model = models.Purchase
        fields = ("gitops_prefix",)

    def clean_gitops_prefix(self):
        prefix = self.cleaned_data.get("gitops_prefix")
        if not prefix:
            raise forms.ValidationError("Value cannot be empty")

        prefix = prefix.lower()
        if not prefix.startswith("http"):
            raise forms.ValidationError("Value is not a URL")

        # when a None instance was passed in __init__() BaseModelForm will
        # create a new model object which isn't yet saved into the database
        if not self.instance.pk:
            raise forms.ValidationError("Subscription required")

        if self.instance.gitops_prefix:
            raise forms.ValidationError(
                "Cannot change existing prefix. Contact Support"
            )

        validate_prefix_against_subscription_plan(prefix, self.instance)

        return prefix
