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

4.7.0 - 2025-01-07
******************
* Gate use of the Xpert platform v2 endpoint with a waffle flag.

4.6.3 - 2025-01-06
******************
* Uses CourseEnrollment instead of CourseMode to get the upgrade deadline required to calculate if a learner's audit trial is expired.
* Updated setup docs

4.6.2 - 2024-12-18
******************
* Fixed the params for expiration_date in the admin table for audit trial.
* Add ENABLE_XPERT_AUDIT instructions.

4.6.1 - 2024-12-17
******************
* Added an admin table for the LearningAssistantAuditTrial model. This table includes an expiration_date valued that is
  calculated based on the start_date.

4.6.0 - 2024-12-10
******************
* Add an audit_trial_length_days attribute to the response returned by the ChatSummaryView, representing the
  number of days in an audit trial as currently configured. It does not necessarily represent the number of days in the
  learner's current trial.

4.5.0 - 2024-12-04
******************
* Add local setup to readme
* Add a BFFE chat summary endpoint for Learning Assistant, including information about whether the Learning Assistant is
  enabled, Learning Assistant message history, and Learning Assistant audit trial data.

4.4.7 - 2024-11-25
******************
* Fixes the Course Chat View CourseMode concatenation issue

4.4.6 - 2024-11-22
******************
* Gates the chat history endpoint behind a waffle flag
* Add LearningAssistantAuditTrial model

4.4.5 - 2024-11-12
******************
* Updated Learning Assistant History payload to return in ascending order

4.4.4 - 2024-11-06
******************
* Fixed Learning Assistant History endpoint
* Added timestamp to the Learning Assistant History payload

4.4.3 - 2024-11-06
******************
* Fixed package version

4.4.2 - 2024-11-04
******************
* Added chat messages to the DB

4.4.1 - 2024-10-31
******************
* Add management command to remove expired messages

4.4.0 - 2024-10-30
******************
* Add LearningAssistantMessage model
* Add new GET endpoint to retrieve a user's message history in a given course.

4.4.0 - 2024-10-25
******************
* Upgraded to use ``Python 3.12``

4.3.3 - 2024-10-15
******************
* Use `LEARNING_ASSISTANT_PROMPT_TEMPLATE` for prompt

4.3.2 - 2024-09-19
******************
* Add error handling for invalid unit usage keys

4.3.1 - 2024-09-10
******************
* Remove GPT model field as part of POST request to Xpert backend

4.3.0 - 2024-07-01
******************
* Adds optional parameter to use updated prompt and model for the chat response.

4.2.0 - 2024-02-28
******************
* Modify call to Xpert backend to prevent use of course index.

4.1.0 - 2024-02-26
******************
* Use course cache to inject course title and course skill names into prompt template.

4.0.0 - 2024-02-21
******************
* Remove use of course waffle flag. Use the django setting LEARNING_ASSISTANT_AVAILABLE
  to enable the learning assistant feature.

3.6.0 - 2024-02-13
******************
* Enable backend access by course waffle flag or django setting.

3.4.0 - 2024-01-30
******************
* Add new GET endpoint to retrieve whether Learning Assistant is enabled in a given course.

3.3.0 - 2024-01-30
******************
* Fix release version

3.2.0 - 2024-01-30
******************
* Remove audit access to chat view.

3.0.1 - 2024-01-29
******************
* Modify gating of learning assistant based on waffle flag and enabled value.

3.0.0 - 2024-01-23
******************
* Remove and drop the course prompt model.

2.0.3 - 2024-01-22
******************
* Remove references to the course prompt model.

2.0.1 - 2024-01-08
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
