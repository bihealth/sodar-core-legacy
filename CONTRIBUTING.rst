.. highlight:: shell

Contributing
^^^^^^^^^^^^

Contributions are welcome, and they are greatly appreciated! Every little bit
helps, and credit will always be given.

You can contribute in many ways:

Types of Contributions
======================

Report Bugs
-----------

Report bugs at https://github.com/bihealth/sodar_core/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
--------

Look through the GitHub issues for bugs. Anything tagged with "bug" and "help
wanted" is open to whoever wants to implement it.

Implement Features
------------------

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
-------------------

SODAR Core could always use more documentation, whether as part of the
official SODAR Core docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
---------------

The best way to send feedback is to file an issue at https://github.com/bihealth/sodar_core/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
============

Ready to contribute? Here's how to set up ``sodar_core`` for local development.

1. Fork the ``sodar_core`` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/sodar_core.git

3. Install your local copy into a virtualenv. Assuming you have virtualenvwrapper installed, this is how you set up your fork for local development::

    $ mkvirtualenv sodar_core
    $ cd sodar_core/
    $ python setup.py develop

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature dev

   Make sure you base your changes on the ``dev`` branch, which is the current
   active development branch. The ``master`` branch is intended for merging
   stable releases only. Now you can make your changes locally.

5. When you're done making changes, make sure to apply proper formatting using
   Black and the settings specified in the accompanying ``black.sh`` script.
   Next, check that your changes pass flake8 and the tests. It is recommended to
   use the accompanying ``test.sh`` script to ensure the correct Django
   configuration is used. For testing other Python versions use tox::

    $ ./black.sh
    $ flake8 .
    $ ./test.sh
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
=======================

Before you submit a pull request, check that it meets these guidelines:

1. Make sure your pull request is up to date with the ``dev`` branch.
2. The pull request should include tests.
3. Black and flake8 should have been executed without errors using settings
   provided in the repo.
4. If the pull request adds functionality, the docs should be updated. Put
   your new functionality into a function with a docstring, and add the
   feature to the list in ``CHANGELOG.rst``.
5. The pull request should work for Python 3.6 and preferably for 3.7. Check
   https://github.com/bihealth/sodar_core/actions
   and make sure that the tests pass for supported Python versions.
   The 1.11 branch of Django does not currently support Python 3.8.

Deploying
=========

A reminder for the maintainers on how to deploy.
Make sure all your changes are committed (including an entry in
``CHANGELOG.rst``). Then run::

$ git tag vX.Y.Z
$ git push
$ git push --tags
$ python setup.py sdist
$ twine upload --repository-url https://test.pypi.org/legacy/ dist/*.tar.gz
$ twine upload dist/*.tar.gz

