import rules


# Predicates -------------------------------------------------------------


# None needed right now


# Rules ------------------------------------------------------------------


# Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------


# Allow viewing site info
rules.add_perm('siteinfo.view_info', rules.is_superuser)
