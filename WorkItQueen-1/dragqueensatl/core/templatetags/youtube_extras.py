from django import template
import re

register = template.Library()

@register.filter
def youtube_embed_id(value):
    """Extract the YouTube video ID from a full YouTube URL."""
    # Example matchers
    regex = r'(?:v=|\/)([0-9A-Za-z_-]{11}).*'
    match = re.search(regex, value)
    if match:
        return match.group(1)
    return value