2. System Prompt Design Changes
###############################

Status
******

**Accepted** *2023-12-13*

Context
*******

A system prompt in the Learning Assistant context refers to the text-based instructions provided to the large language 
model (LLM) that describe the objective and proper behavior of the Learning Assistant. This prompt is provided to the
LLM via 2U's Xpert Platform generic chat completion endpoint as the first set of elements in the ``message_list``
payload key.

Currently, the system prompt is stored in the `CoursePrompt model`_ on a per-course basis. For each course in which the
Learning Assistant is enabled, a system prompt must be stored in the associated database table.

The original intention behind storing the system prompt in this way was to enable an expedited release, a greater degree
of per-course customization, and a flexibility to modify the system prompt quickly in the early stages of the project.

The process of releasing the Learning Assistant to a new course involves either the manual creation of the model
instance via the Django admin or the use of the `set_course_prompts management command`_. The latter requires that a
member of 2U's Site Reliability Engineering (SRE) team runs this command in the proper environment.

The next iteration of the Learning Assistant will enable the integration of unit content into the system prompt to
provide the LLM with more information about the context in which the learner is asking a question. This will require a
change to the system prompt to accommodate the unit content, and will, thus, require manual work on the part of an
engineer to update the existing system prompts and to create new system prompts as we approach a full roll out. This
presents an opportunity to reconsider the way that we store and process the system prompt.

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