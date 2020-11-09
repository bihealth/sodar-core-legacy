.. _user_stories:

============
User Stories
============

This section explains how SODAR Core based web applications are built on a very high level.
We assume that you have read the :ref:`for_the_impatient` section and are basing your web application on the SODAR Core example site as described there.
Also, we assume that you have intermediate experience with Django and Python programming.

Please also note that the term *web app* refers to the overall *Django site*, that is what the user sees and what is commonly referred to as a "web application" or "dynamic website".
The term *Django app* refers to the technical term within Django development, that is a "Django app Python package".

-------------------------
Flow Cell Data Management
-------------------------

On a very high level here is how SODAR Core was used to built Digestiflow (cf. :ref:`for_the_impatient_see_it_in_action`).
You can find the source code in the `Github project <https://github.com/bihealth/digestiflow-server>`__.

The aim is to manage the meta data for sequencers and flow cells.

SODAR Core App Configuration
============================

- Configure your Django site to use the ``projectroles`` SODAR Core Django app.
  Each SODAR Core "project" corresponds to one site and this would allow to have multiple groups manage their sequencing meta data in the same web app instance.
- Configure the ``timeline`` SODAR Core Django app to provide an audit trail of changes to data.
- Configure the ``filesfolders`` SODAR Core Django app to manage small file uploads in various places.

Custom Apps
===========

The following description uses domain-specific language from the high-throughput sequencing domain.
While this makes the section harder to understand to the layperson, explaining the different terms is out of scope in this manual.

- Write the ``sequencers`` app for management of sequencing machines.
- Write the ``barcodes`` app for management of the barcode adapter sets.
- Write the ``flowcells`` app for managing flow cells and libraries.
  This app depends on ``sequencers`` and ``barcodes`` for these apps' Django models.

----------------
Variant Analysis
----------------

On a very high level here is how SODAR Core was used to built VarFish (cf. :ref:`for_the_impatient_see_it_in_action`).
You can find the source code in the `Github project <https://github.com/bihealth/varfish-server>`__.

The aim is to provide an data analysis web application.

SODAR Core App Configuration
============================

- Configure your Django site to use the ``projectroles`` SODAR Core Django app.
  Each SODAR Core "project" corresponds to one site and this would allow to have multiple groups manage their sequencing meta data in the same web app instance.
- Configure the ``timeline`` SODAR Core Django app to provide an audit trail of changes to data.
- Configure the ``bgjobs`` SODAR Core Django app to manage asynchronous jobs, such as long-running queries.

Custom Apps
===========

The following description uses domain-specific language from the medical genetics domain.
While this makes the section harder to understand to the layperson, explaining the different terms is out of scope in this manual.

- Write various Django apps for importing background data such as population frequencies from the gnomAD project, genes, etc.
- Write the ``variants`` app to implement the actual variant filtration.
  This is the core part of Varfish and provides the different Django models, views, and templates to actually perform the variant filtration.
- Write the ``importer`` app to implement efficient bulk import of variants from annotated TSV files.
