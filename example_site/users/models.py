# Projectroles dependency
from projectroles.models import SODARUser


# The User model should be derived from the abstract SODARUser model. Add custom
# fields and functions as needed.

# NOTE: If integrating projectroles with an existing project, you will have to
#       include migration scripts for populating the sodar_uuid field. See:
#


class User(SODARUser):
    pass
