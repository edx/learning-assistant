"""
Contain all imported functions coming out of the platform.

We know these functions will be available at run time, but they
cannot be imported normally.
"""


def get_text_transcript(video_block):
    """Get the transcript for a video block in text format, or None."""
    # pylint: disable=import-error, import-outside-toplevel
    from xmodule.exceptions import NotFoundError
    from xmodule.video_block.transcripts_utils import get_transcript
    try:
        transcript, _, _ = get_transcript(video_block, output_format='txt')
    except NotFoundError:
        # some old videos have no transcripts, just accept that reality
        return None
    return transcript


def get_single_block(request, user_id, course_id, usage_key_string, course=None):
    """Load a single xblock."""
    # pylint: disable=import-error, import-outside-toplevel
    from lms.djangoapps.courseware.block_render import load_single_xblock
    return load_single_xblock(request, user_id, course_id, usage_key_string, course)


def traverse_block_pre_order(start_node, get_children, filter_func=None):
    """Traverse a DAG or tree in pre-order."""
    # pylint: disable=import-error, import-outside-toplevel
    from openedx.core.lib.graph_traversals import traverse_pre_order
    return traverse_pre_order(start_node, get_children, filter_func)


def block_leaf_filter(block):
    """Return only leaf nodes."""
    # pylint: disable=import-error, import-outside-toplevel
    from openedx.core.lib.graph_traversals import leaf_filter
    return leaf_filter(block)


def block_get_children(block):
    """Return children of a given block."""
    # pylint: disable=import-error, import-outside-toplevel
    from openedx.core.lib.graph_traversals import get_children
    return get_children(block)


def get_cache_course_run_data(course_run_id, fields):
    """
    Return course run related data given a course run id.

    This function makes use of the discovery course run cache, which is necessary because
    only the discovery service stores the relation between courseruns and courses.
    """
    # pylint: disable=import-error, import-outside-toplevel
    from openedx.core.djangoapps.catalog.utils import get_course_run_data
    return get_course_run_data(course_run_id, fields)
