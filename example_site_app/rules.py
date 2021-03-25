import rules

# Projectroles dependency
from projectroles import rules as pr_rules  # To access common predicates


# Predicates -------------------------------------------------------------


# None needed right now


# Rules ------------------------------------------------------------------


# Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------


# Allow viewing data (note: also OK for anonymous)
rules.add_perm(
    'example_site_app.view_data',
    rules.is_authenticated | pr_rules.is_allowed_anonymous,
)
