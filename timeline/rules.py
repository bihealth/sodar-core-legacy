"""Access rules for the timeline app"""

import rules

# Projectroles dependency
from projectroles import rules as pr_rules  # To access common predicates


# Predicates -------------------------------------------------------------


# If we need to assign new predicates, we do it here


# Rules ------------------------------------------------------------------


# Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------


# Allow viewing project timeline
rules.add_perm(
    'timeline.view_timeline',
    pr_rules.is_project_owner
    | pr_rules.is_project_delegate
    | pr_rules.is_project_contributor
    | pr_rules.is_project_guest,
)

# Allow viewing timeline for site-specific events
rules.add_perm('timeline.view_site_timeline', rules.is_authenticated)

# Allow viewing classified event
rules.add_perm(
    'timeline.view_classified_event',
    pr_rules.is_project_owner | pr_rules.is_project_delegate,
)

# Allow viewing classified site-wide event
rules.add_perm('timeline.view_classified_site_event', rules.is_superuser)
