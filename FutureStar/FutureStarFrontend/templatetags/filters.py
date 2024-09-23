from django import template

register = template.Library()

@register.filter
def get_language_field(value, lang):
    """
    Appends the language suffix (like _en or _ar) to the field name dynamically.
    Example: {{ news_item|get_language_field:current_language }}
    """
    field_name = f"{value}_{lang}"
    return getattr(value, field_name, "")
