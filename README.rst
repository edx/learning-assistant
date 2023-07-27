learning-assistant
#############################

|pypi-badge| |ci-badge| |codecov-badge| |doc-badge| |pyversions-badge|
|license-badge| |status-badge|

Purpose
*******

Plugin for a learning assistant backend, intended for use within edx-platform.

This library contains data models and logic for a platform wide learning assistant.

Dependencies
************
In addition to the edx-platform repository in which this library is installed, this plugin also
leverages the `frontend-lib-learning-assistant`_ as a frontend interface for the learning assistant.

Getting Started
***************

Developing
==========

One Time Setup
--------------
.. code-block::

  # Clone the repository
  git clone git@github.com:openedx/learning-assistant.git
  cd learning-assistant

  # Set up a virtualenv with the same name as the repo and activate it
  # Here's how you might do that if you have virtualenvwrapper setup.
  mkvirtualenv -p python3.8 learning-assistant

Every time you develop something in this repo
---------------------------------------------
.. code-block::

  # Activate the virtualenv
  # Here's how you might do that if you're using virtualenvwrapper.
  workon learning-assistant

  # Grab the latest code
  git checkout main
  git pull

  # Install/update the dev requirements
  make requirements

  # Run the tests and quality checks (to verify the status before you make any changes)
  make validate

  # Make a new branch for your changes
  git checkout -b <your_github_username>/<short_description>

  # Using your favorite editor, edit the code to make your change.
  vim ...

  # Run your new tests
  pytest ./path/to/new/tests

  # Run all the tests and quality checks
  make validate

  # Commit all your changes
  git commit ...
  git push

  # Open a PR and ask for review.

License
*******

The code in this repository is licensed under the AGPL 3.0 unless
otherwise noted.

Please see `LICENSE.txt <LICENSE.txt>`_ for details.

Contributing
************

This repo is not currently accepting contributions.

The Open edX Code of Conduct
****************************

All community members are expected to follow the `Open edX Code of Conduct`_.

.. _Open edX Code of Conduct: https://openedx.org/code-of-conduct/

Reporting Security Issues
*************************

Please do not report security issues in public. Please email security@edx.org.

.. |pypi-badge| image:: https://img.shields.io/pypi/v/learning-assistant.svg
    :target: https://pypi.python.org/pypi/learning-assistant/
    :alt: PyPI

.. |ci-badge| image:: https://github.com/openedx/learning-assistant/workflows/Python%20CI/badge.svg?branch=main
    :target: https://github.com/openedx/learning-assistant/actions
    :alt: CI

.. |codecov-badge| image:: https://codecov.io/github/openedx/learning-assistant/coverage.svg?branch=main
    :target: https://codecov.io/github/openedx/learning-assistant?branch=main
    :alt: Codecov

.. |doc-badge| image:: https://readthedocs.org/projects/learning-assistant/badge/?version=latest
    :target: https://docs.openedx.org/projects/learning-assistant
    :alt: Documentation

.. |pyversions-badge| image:: https://img.shields.io/pypi/pyversions/learning-assistant.svg
    :target: https://pypi.python.org/pypi/learning-assistant/
    :alt: Supported Python versions

.. |license-badge| image:: https://img.shields.io/github/license/openedx/learning-assistant.svg
    :target: https://github.com/openedx/learning-assistant/blob/main/LICENSE.txt
    :alt: License

.. TODO: Choose one of the statuses below and remove the other status-badge lines.
.. |status-badge| image:: https://img.shields.io/badge/Status-Experimental-yellow
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Maintained-brightgreen
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Deprecated-orange
.. .. |status-badge| image:: https://img.shields.io/badge/Status-Unsupported-red

.. _frontend-lib-learning-assistant: https://github.com/edx/frontend-lib-learning-assistant
