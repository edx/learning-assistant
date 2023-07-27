0001 Purpose of This Repo
#########################

Status
******

**Accepted** 07/27/2023

Context
*******

In order to support a platform learning assistant, a new Django app should be created to store
data related to the learning assistant, including data for each course in which the learning assistant is enabled, and learner data related to
interactions with the learning assistant.

Decision
********

We will create a repository configured as a django plugin, meant for installation in the edx-platform repository. Using the plugin architecture will
allow us to make this feature optional for Open edX deployers, while still allowing the plugin to utilize functionality from the platform itself.

Consequences
************

- learning-assistant does not have to be enabled for every Open edX instance
- edx-platform will not import directly from learning-assistant
- learning-assistant can import functions from edx-platform

Rejected Alternatives
*********************

**edx-platform app**

- Create a new application directly in `edx-platform`.
- This is the easiest option, but couples the code to platform.
- No option for Open edX community to opt out.

**Django plugin**

- Decoupled from `edx-platform`, and better ability for open edX to opt out.
- `learning-assistant` can import functionality directly from `edx-platform`.
- Release will still depend on `edx-platform`.

**IDA**

- Decoupled from `edx-platform`, and better ability for open edX to opt out.
- It has a more involved setup, but would result in a faster deployment process.
- Because this application is intended to be small, a separate service might be overkill.
