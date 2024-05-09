#
# Copyright (c) 2024 Alexander Todorov <atodorov@MrSenko.com>
#
# Licensed under the GPL 3.0: https://www.gnu.org/licenses/gpl-3.0.txt

from django import forms
from django.utils.translation import gettext_lazy as _

from tcms_github_marketplace import models


class UpdateGitopsPrefixForm(forms.ModelForm):
    class Meta:
        model = models.Purchase
        fields = ("gitops_prefix",)

    def clean_gitops_prefix(self):
        prefix = self.cleaned_data.get("gitops_prefix")

        if not prefix:
            raise forms.ValidationError(_("Value cannot be empty"))

        if not prefix.lower().startswith("http"):
            raise forms.ValidationError(_("Value is not an HTTP URL"))

        return prefix
