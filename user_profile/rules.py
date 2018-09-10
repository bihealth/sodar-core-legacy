import rules


# Predicates -------------------------------------------------------------


# None needed right now


# Rules ------------------------------------------------------------------


# Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------


# Allow viewing user detail
rules.add_perm(
    'user_profile.view_detail',
    rules.is_authenticated)
