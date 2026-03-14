# Copyright (c) 2026 Alexander Todorov <atodorov@otb.bg>
#
# Licensed under GNU Affero General Public License v3 or later (AGPLv3+)
# https://www.gnu.org/licenses/agpl-3.0.html

import requests
from requests.auth import AuthBase
from httplink import parse_link_header


class TokenAuth(AuthBase):
    def __init__(self, token):
        self.token = token

    def __eq__(self, other):
        return self.token == getattr(other, "token", None)

    def __ne__(self, other):
        return not self == other

    def __call__(self, r):
        r.headers["Authorization"] = f"Bearer {self.token}"
        return r


class GemfuryAPI:
    base_url = "https://api.fury.io/1"

    def __init__(self, password=None):
        """
        WARNING: we must be using the Full Access Token on the organization account!
        """
        self.auth = TokenAuth(password)

    def find_token(self, subscription_id):
        json_data, link = self._request("GET", "/tokens?kind_key=pull")

        while json_data:
            for token in json_data:
                if token.get("description") == subscription_id:
                    return token

            if link:
                page = parse_link_header(link)
                # keep asking for content until there's no-more
                if "next" in page:
                    next_url = page["next"].target
                    json_data, link = self._request("GET", f"/tokens{next_url}")
                else:
                    break
            else:
                break

        return None

    def create_token(self, subscription_id):
        """
        Returns:

        {
            'token': {
                'id': 'tok_MBFav',
                'kind_key': 'pull'
            },
            'token_value': 'actual-value'
        }
        """
        json_response, _ = self._request(
            "POST", f"/tokens?kind_key=pull&description={subscription_id}"
        )
        return json_response

    def delete_token(self, subscription_id):
        token = self.find_token(subscription_id)

        if token and token.get("id"):
            token_id = token["id"]
            # returns None, None
            self._request("DELETE", f"/tokens/{token_id}")

    def _request(self, method, path, **kwargs):
        """
        https://gemfury.com/guide/api/errors/
        """
        response = requests.request(
            method,
            f"{self.base_url}{path}",
            auth=self.auth,
            timeout=30,
            **kwargs,
        )

        # Successful operation with no body
        if response.status_code == 204:
            return None, None

        return response.json(), response.headers.get("Link")
