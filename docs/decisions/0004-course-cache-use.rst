4. Use of the LMS course caches
###############################

Status
******

**Accepted** *2024-02-26*

Context
*******
Each course run ID in edx-platform is associated with another course ID. While for many courses, the mapping between
course run ID and course ID is straight forward, i.e. edX+testX+2019 -> edX+testX, this is not the case for every
course on edX. The discovery service is the source of truth for mappings between course run ID and course IDs, and
string manipulation cannot be relied on as an accurate way to map between the two forms of ID.

The learning-assistant `CourseChatView`_ accepts a course run ID as a path parameter, but a number of API functions
in the learning assistant backend also require the course ID associated with a given course.

In our initial release, we also found that the current courses available in 2U's Xpert Platform team's index, which was
being used to inject course skill names and course titles into the system prompt (see `System Prompt Design Changes`_ for
original details), were too limited. Courses included in that index were conditionally added depending on course
enrollment dates and additional fields from the discovery course API. While the 2U Xpert Platform team may work to address
the gap in product needs for their current course index, an alternate method for retrieving course skills and title should
be considered.

Decision
********
In order to determine the mapping between a course run ID and course ID in the learning-assistant app, we will make
use of an `existing course run cache that is defined in edx-platform`_. Similarly, to retrieve the skill names and title of a course, we will also use
an `existing course cache`_. Both caches store data from the discovery API for course runs and courses, respectively.
These are long term caches with a TTL of 24 hours, and on a cache miss the discovery API will be called.

Consequences
************
* If the caches were to be removed, code in the learning-assistant repository would no longer function as expected.
* On a cache miss, the learning-assistant backend will incur additional performance cost on calls to the discovery API.

Rejected Alternatives
*********************
* Calling the discovery API directly from the learning-assistant backend
    * This would require building a custom solution in the learning-assistant app to call the discovery service directly.
    * Without a cache, this would impact performance on every call to the learning-assistant backend.
* Using string manipulation to map course run ID to course ID.
    * If we do not use the discovery service as our source of truth for course run ID to course ID mappings,
      we run the risk of being unable to support courses that do not fit the usual pattern mapping.

.. _existing course run cache that is defined in edx-platform: https://github.com/openedx/edx-platform/blob/c61df904c1d2a5f523f1da44460c21e17ec087ee/openedx/core/djangoapps/catalog/utils.py#L801
.. _CourseChatView: https://github.com/edx/learning-assistant/blob/fddf0bc27016bd4a1cabf82de7bcb80b51f3763b/learning_assistant/views.py#L29
.. _System Prompt Design Changes: https://github.com/edx/learning-assistant/blob/main/docs/decisions/0002-system-prompt-design-changes.rst
.. _existing course cache: https://github.com/openedx/edx-platform/blob/3a2b6dd8fcc909fd9128f81750f52650ba8ff906/openedx/core/djangoapps/catalog/utils.py#L767
