# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/edx/learning-assistant/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                                                                          |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|------------------------------------------------------------------------------ | -------: | -------: | -------: | -------: | ------: | --------: |
| learning\_assistant/\_\_init\_\_.py                                           |        2 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/api.py                                                    |      109 |        2 |       14 |        1 |     98% |120->130, 208-209 |
| learning\_assistant/apps.py                                                   |        4 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/constants.py                                              |        6 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/data.py                                                   |       12 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/management/\_\_init\_\_.py                                |        0 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/management/commands/\_\_init\_\_.py                       |        0 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/management/commands/retire\_user\_messages.py             |       26 |        0 |        2 |        0 |    100% |           |
| learning\_assistant/management/commands/tests/\_\_init\_\_.py                 |        0 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/management/commands/tests/test\_retire\_user\_messages.py |       21 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/migrations/0001\_initial.py                               |        8 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/migrations/0002\_alter\_courseprompt\_prompt.py           |        4 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/migrations/0003\_courseprompt\_json\_prompt\_content.py   |        4 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/migrations/0004\_remove\_courseprompt\_prompt.py          |        4 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/migrations/0005\_learningassistantcourseenabled.py        |        7 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/migrations/0006\_delete\_courseprompt.py                  |        4 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/migrations/0007\_learningassistantmessage.py              |        9 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/migrations/0008\_alter\_learningassistantmessage\_role.py |        4 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/migrations/0009\_learningassistantaudittrial.py           |        8 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/migrations/\_\_init\_\_.py                                |        0 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/models.py                                                 |       19 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/platform\_imports.py                                      |       29 |       21 |        0 |        0 |     28% |12-19, 25-26, 32-33, 39-40, 46-47, 58-59, 70-71, 86-87 |
| learning\_assistant/plugins\_api.py                                           |       16 |        0 |        2 |        0 |    100% |           |
| learning\_assistant/serializers.py                                            |       14 |        1 |        2 |        1 |     88% |        36 |
| learning\_assistant/text\_utils.py                                            |       32 |        2 |        4 |        1 |     86% |42->exit, 47-48 |
| learning\_assistant/toggles.py                                                |       13 |        2 |        0 |        0 |     85% |    34, 43 |
| learning\_assistant/urls.py                                                   |        5 |        0 |        0 |        0 |    100% |           |
| learning\_assistant/utils.py                                                  |       78 |        0 |       16 |        0 |    100% |           |
| learning\_assistant/views.py                                                  |      130 |        9 |       26 |        1 |     94% |20-23, 88, 128-129, 256-257 |
|                                                                     **TOTAL** |  **568** |   **37** |   **66** |    **4** | **93%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/edx/learning-assistant/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/edx/learning-assistant/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/edx/learning-assistant/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/edx/learning-assistant/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2Fedx%2Flearning-assistant%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/edx/learning-assistant/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.