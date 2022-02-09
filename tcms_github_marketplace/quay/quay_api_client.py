import logging

from .quay_session import QuaySession

LOG = logging.getLogger("pubtools.quay")


class QuayApiClient:
    """Class for performing Quay REST API queries."""

    def __init__(self, token, host=None):
        """
        Initialize.

        Args:
            token (str):
                Quay API token for authentication.
            host (str):
                Quay registry URL.
        """
        self.token = token
        self.session = QuaySession(hostname=host, verify=True, api="quay")
        self.session.set_auth_token(self.token)

    def get_robot_from_organization(self, robot_shortname, orgname):
        """
        Get information about a robot account in the organization.
        """
        endpoint = f"organization/{orgname}/robots/{robot_shortname}"
        response = self.session.get(endpoint)

        json = response.json()
        if (
            "message" in json
            and json["message"] == "Could not find robot with specified username"
        ):
            return None

        return json

    def create_robot_in_organization(self, robot_shortname, orgname):
        """
        Create a robot account in the organization.
        """
        endpoint = f"organization/{orgname}/robots/{robot_shortname}"
        response = self.session.put(
            endpoint, json={"unstructured_metadata": {}, "description": ""}
        )

        return response.json()

    def delete_robot_from_organization(self, robot_shortname, orgname):
        """
        Delete a robot account from the organization.

        Returns empty text on success, otherwise it's a JSON error message
        """
        endpoint = f"organization/{orgname}/robots/{robot_shortname}"
        response = self.session.delete(endpoint)

        return response.text

    def update_user_permissions(self, username, repository, role="read"):
        """
        Update the perimssions for an existing repository.
        """
        endpoint = f"repository/{repository}/permissions/user/{username}"
        response = self.session.put(endpoint, json={"role": role})

        return response.json()

    def regenerate_robot_token(self, robot_shortname, orgname):
        endpoint = f"organization/{orgname}/robots/{robot_shortname}/regenerate"
        response = self.session.post(endpoint)
        return response.json()
