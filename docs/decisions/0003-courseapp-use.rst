3. CourseApp Use
################

Status
******

**Accepted** *2024-01-05*

Context
*******

We are adding the ability for course teams to manually enable and disable the Learning Assistant in their courses via
a card in the Pages & Resources page of Studio, provided that the Learning Assistant is enabled and available in their
course.

The Pages & Resources page is powered on the backend by the edX Platform CourseApp application. That is, with one
exception in the case of AI Summaries, each card on the Pages & Resources page has a corresponding instance of the 
CourseApp plugin configured in the platform. The Pages & Resources page can then make calls to the backend CourseApp
API to get necessary information about the feature described by the plugin.

Currently, 

Decision
********

* We will store a system prompt template in a Django setting in the form of a Jinja template.
* We will use Jinja constructs, such as variables and control structures, to implement a single system prompt template
  for all courses.
* The system prompt template will be rendered in two steps.
  
  * The first render step will be performed by the `learning-assistant`_ code. This step will interpolate any variables
    for which this code has a value (e.g. unit content).
  * The second render step will be performed by the 2U Xpert Platform generic chat completion endpoint. This step will
    interpolate any variable for which the platform has a value (e.g. course title and skill names).

* After the first render step, the resulting value will be a Jinja template that has been partially rendered. This
  template will be sent to 2U's Xpert Platform generic chat completion endpoint to be completely rendered.
* We will remove the `CoursePrompt model`_ following the instructions documented in
  `Everything About Database Migrations`_.

Consequences
************

* Changes to the system prompt will require pull requests to the appropriate repository in which the prompt is stored.
* Anyone with access to the appropriate repository in which the prompt is stored can change the system prompt. Members
  of the team will no longer require assistance from the SRE team.
* The transition to a system prompt template required the 2U Xpert Platform team to provide support for accepting and 
  rendering a system prompt template and the integration of Discovery ``skill_names`` into their index.
* The use of a system prompt template will require cross-team collaboration to ensure that the same variable names are
  use in the system prompt template, in the `learning-assistant`_ code, and the 2U Xpert Platform generic chat
  completion endpoint.
* Because the system prompt template will be stored in a Django setting in a private repository, and the code that
  renders the template is stored here, changes to the template will require careful coordination to ensure that the
  template is rendered properly.

  * For example, if a new variable is added to the template, the code must be modified and deployed in advanced of
    changes to the template. Otherwise, if changes to template are deployed before the related code changes, then the
    rendered template will contain uninterpolated variables.

* It will become more difficult to enable per-course customizations because all courses will be served by a single
  system prompt template.

Rejected Alternatives
*********************

* Status Quo

  * The main alternative to this change is to continue to use manual entry and the `set_course_prompts management command`_
    to manage system prompts.
  * To enable unit content integration, we would need to modify the JSON string stored in the `CoursePrompt model`_ to
    store a JSON string with format string variable for the content, which would be interpolated at runtime.
  * The main advantage of this alternative is that it will require less engineering work.
  * The main disadvantage of this alternative is that it will become challenging to manage which prompt a course should
    use. For example, to do a stage released of unit content integration, we would be required to manage different
    templates manually. Later, a full release would require additional changes. This would make management of the
    templates even more tedious.
  * Managing system prompts in a full release would become intractable.
  * Additionally, in order to better operationalize the use of the management command and to reduce our reliance on the
    SRE team, we would likely want to invest time in setting up a Jenkins job to run the management command ad-hoc. If
    we will be investing engineering resources in this area anyway, we felt it was a more future-proof approach to
    pursue the solution described above.

.. _set_course_prompts management command: https://github.com/edx/learning-assistant/blob/main/learning_assistant/management/commands/set_course_prompts.py
.. _CoursePrompt model: https://github.com/edx/learning-assistant/blob/34604a0775f7bd79adb465e0ca51c7759197bfa9/learning_assistant/models.py
.. _Everything About Database Migrations: https://openedx.atlassian.net/wiki/spaces/AC/pages/23003228/Everything+About+Database+Migrations#EverythingAboutDatabaseMigrations-Howtodropatable
.. _learning-assistant: https://github.com/edx/learning-assistant