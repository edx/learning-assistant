Change Log
##########

..
   All enhancements and patches to learning_assistant will be documented
   in this file.  It adheres to the structure of https://keepachangelog.com/ ,
   but in reStructuredText instead of Markdown (for ease of incorporation into
   Sphinx documentation and the PyPI description).

   This project adheres to Semantic Versioning (https://semver.org/).

.. There should always be an "Unreleased" section for changes pending release.

Unreleased
**********

2.0.1 - 2021-01-08
******************
* Gate content integration with waffle flag

2.0.0 - 2024-01-03
******************
* Add content cache
* Integrate system prompt setting

1.5.0 - 2023-10-18
******************
* Add management command to generate course prompts

1.4.0 - 2023-09-11
******************
* Send reduced message list if needed to avoid going over token limit

1.3.3 - 2023-09-07
******************
* Allow any enrolled learner to access API.

1.3.2 - 2023-08-25
******************
* Remove deserialization of prompt field, as it is represented in the python
  native format

1.3.1 - 2023-08-24
******************
* Remove prompt field

1.3.0 - 2023-08-24
******************
* Remove references to prompt field
* Create json_prompt field to allow for more flexible prompts

1.2.1 - 2023-08-24
******************
* make prompt field nullable

1.2.0 - 2023-08-22
******************
* add endpoint authentication
* fix request structure required for endpoint integration

1.1.0 - 2023-08-09
******************
* fix for course id to course key conversion

1.0.0 - 2023-08-08
******************

* Add endpoint to retrieve chat response
* Created model to associate course ideas with a specific prompt text

Unreleased
**********


0.1.0 – 2023-07-26
**********************************************

Added
=====

* First release on PyPI.
