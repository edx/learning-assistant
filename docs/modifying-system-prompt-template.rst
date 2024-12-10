Modifying the System Prompt Template
####################################

Context
*******

Because the system prompt template will be stored in a Django setting in a private repository, and the code that
renders the template is stored here, changes to the template will require careful coordination to ensure that the
template is rendered properly.

For example, if a new variable is added to the template, the code must be modified and deployed in advanced of
changes to the template. Otherwise, if changes to template are deployed before the related code changes, then the
rendered template will contain uninterpolated variables.

This document describes how to properly modify the system prompt template and the code that renders it. These steps
are only required when your change introduces a new dependency between the template and the code. For example, the
introductin of a new variable introduces a new dependency, because the code must provide the value for this variable
when the template is rendered for the variable to be interpolated properly. Additionally, renaming a variable or
removing a variable would also require you to follow these steps. On the other hand, using an existing variable in a new
way or changing static text in the template would not require you to follow these steps, because these changes would not
require a related change to the code.

Adding to the Template
**********************

If you are adding to the template, then you must follow these steps.

#. Modify the code to supply the correct values to the function that renders the template.
#. Merge and deploy the code changes.
#. Modify the template.
#. Merge and deploy the template changes.

Removing From the Template
**************************

If you are removing from the template, then you must follow these steps.

#. Modify the template.
#. Merge and deploy the template changes.
#. Modify the code to supply the correct values to the function that renders the template.
#. Merge and deploy the code changes.

Adding to and Removing From the Template
****************************************

Combination changes will require that the changes are divided into additions and removals. Divide your changes into
additions and removals and follow the above steps for adding to the template and removing from the template,
respectively.
