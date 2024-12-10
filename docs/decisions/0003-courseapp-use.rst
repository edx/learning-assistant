3. CourseApp Use
################

Status
******

**Accepted** *2024-01-08*

Context
*******

We are adding the ability for course teams to manually enable and disable the Learning Assistant in their courses via
a card in the `Pages & Resources page`_ of Studio, provided that the Learning Assistant is enabled and available in
a given course.

The `Pages & Resources page`_ is powered on the backend by the edX Platform `CourseApp Django app`_. With one
exception in the case of Xpert Unit Summaries, each card on the `Pages & Resources page`_ has a corresponding instance
of the `CourseApp plugin`_ configured in the `edx-platform repository`_. The `Pages & Resources page`_ can then make
calls to the `backend CourseApp REST API`_ to get necessary information about the feature described by the plugin.

The one exception to this behavior is the ``Xpert unit summaries card``, which uses a `Javascript object`_ stored in a
static file in the `frontend-app-course-authoring repository`_ to describe the options that would otherwise be returned
by the `backend CourseApp REST API`_ using a corresponding ``CourseApp`` plugin.

Currently, the only ``CourseApp`` plugins registered in the platfrom are those that are defined within the
`edx-platform repository`_. There are currently no plugins that are defined outside of the `edx-platform repository`_.

Decision
********

* We will define an instance of the `CourseApp plugin`_ in this repository to describe the Learning Assistant feature.
* We will register the `CourseApp plugin`_ as an entrypoint with the ``openedx.course_app`` key so that the `CourseApp
  Django app`_ will be able to pick up the plugin if the Learning Assistant plugin is installed into ``edx-platform``.

Consequences
************

* The Learning Assistant ``CourseApp`` plugin will only be registered with the `CourseApp Django app`_ if, and,
  therefore, the Learning Assistant card on the `Pages & Resources page`_ will only be visible if, the Learning
  Assistant plugin is installed into ``edx-platform``.
* It will become slightly more difficult to know which ``CourseApps`` are available simply by reading the code, because
  this ``CourseApp`` plugin is not stored in the `edx-platform repository`_.
* Because the `CourseApps` API is registered under the CMS application, the Learning Assistant needs to be registered as
  a plugin to the CMS as well. Otherwise, the plugin is not included in the CMS application's ``INSTALLED_APPS`` list.
  This causes a runtime error, because the Learning Assistant CourseApp plugin will refer to the Learning Assistant's
  models, and this are not available in the CMS if the Learning Assistant plugin is not installed.

Rejected Alternatives
*********************

* We decided not to add in a custom backend REST API for exposing the ability to introspect the Learning Assistant
  feature and enable and disable it. There already exists the `CourseApp Django app`_ for this purpose, and using it
  allows us to avoid writing a lot of ad hoc code.

.. _backend CourseApp REST API: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/course_apps/rest_api/v1/views.py#L80
.. _CourseApp Django app: https://github.com/openedx/edx-platform/tree/master/openedx/core/djangoapps/course_apps
.. _CourseApp plugin: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/course_apps/plugins.py#L15
.. _edx-platform: https://github.com/openedx/edx-platform
.. _edx-platform repository: https://github.com/openedx/edx-platform
.. _frontend-app-course-authoring repository: https://github.com/openedx/frontend-app-course-authoring/tree/master
.. _Javascript object: https://github.com/openedx/frontend-app-course-authoring/blob/master/src/pages-and-resources/xpert-unit-summary/appInfo.js
.. _Pages & Resources page: https://github.com/openedx/frontend-app-course-authoring/tree/master/src/pages-and-resources
