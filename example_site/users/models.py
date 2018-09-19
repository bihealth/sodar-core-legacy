# Projectroles dependency
from projectroles.models import OmicsUser


# The User model should be derived from the abstract OmicsUser model. Add custom
# fields and functions as needed.

# NOTE: If integrating projectroles with an existing project, you will have to
#       include migration scripts for populating the sodar_uuid field. See:
#


class User(OmicsUser):
    pass
