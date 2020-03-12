from django import template

register = template.Library()


@register.simple_tag
def active(request, pattern):
    if pattern == request.path:
        return 'active'
    return ''


@register.filter(name='get_item')
def get_item(dictionary, key):
    return dictionary.get(key)
