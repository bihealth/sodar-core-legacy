"""Rules for the appalerts app"""

import rules


# Predicates -------------------------------------------------------------


# None needed right now


# Rules ------------------------------------------------------------------


# Rules should not be needed, use permissions for user rights


# Permissions ------------------------------------------------------------

# Allow viewing alerts
rules.add_perm('appalerts.view_alerts', rules.is_authenticated)
