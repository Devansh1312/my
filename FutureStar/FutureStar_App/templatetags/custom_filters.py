from django import template
import os

register = template.Library()

@register.filter(name='add_class')
def add_class(value, css_class):
    return value.as_widget(attrs={'class': css_class})



@register.filter
def get_language_field(value, lang):
    """
    Appends the language suffix (like _en or _ar) to the field name dynamically.
    Example: {{ news|get_language_field:selected_language }}
    """
    field_name = f"{value}_{lang}"
    return getattr(value, field_name, "")


@register.filter
def get_filename(value):
    """
    Returns the file name from a file path.
    """
    return os.path.basename(value)