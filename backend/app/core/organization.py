"""Validation shared by organization-scoped service entry points."""


def validate_organization_id(organization_id):
    """Return a valid organization ID or fail closed."""
    if (
        not isinstance(organization_id, int)
        or isinstance(organization_id, bool)
        or organization_id <= 0
    ):
        raise ValueError("A valid organization_id is required.")
    return organization_id
