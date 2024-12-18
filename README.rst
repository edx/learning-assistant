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

  # Clone the repository (in the ../src relative to devstack repo)
  git clone git@github.com:openedx/learning-assistant.git
  cd learning-assistant

  # Set up a virtualenv with the same name as the repo and activate it
  # Here's how you might do that if you have virtualenvwrapper setup.
  mkvirtualenv -p python3.8 learning-assistant

In your ``requirements/edx/private.txt`` requirements file in edx-platform, add:

.. code-block::

  -e /edx/src/learning-assistant

In your ``lms/envs/private.py`` settings file in edx-platform (create file if necessary), add the below settings. The value of the API key shouldn't matter, because it's not being used at this point, but the setting needs to be there.

.. code-block::

  CHAT_COMPLETION_API = '' # copy url from edx-internal
  CHAT_COMPLETION_API_KEY = '' # add value though value itself does not matter

  LEARNING_ASSISTANT_PROMPT_TEMPLATE = '' # copy value from edx-internal

  LEARNING_ASSISTANT_AVAILABLE = True

In devstack, run ``make lms-shell`` and run the following command: ``paver install_prereqs;exit``. This will install anything included in your ``private.txt`` requirements file.

In django admin, add the following waffle flag ``learning_assistant.enable_course_content`` and make sure it is turned on for Everyone. The flag should be checked on for: Superusers, Staff, and Authenticated.

This plugin depends on the lms and discovery - both should be running.

Enabling Xpert for audit learners
---------------------------------
In addition to the "One Time Setup" instructions, the following instructions should be followed to enable Xpert for audit learners locally.
In your ``env.development`` config file in frontend-app-learning, add the below setting.

.. code-block::

  ENABLE_XPERT_AUDIT='true'

Ensure that you have a non-expired verified mode set up locally for your testing course. You can do this by checking if http://localhost:18000/admin/course_modes/coursemode/ has a course mode with a future expiration date.

The Xpert for audit learner frontend code depends on the lms, discovery, and ecommerce services. Ensure that all three services are running without errors.

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
