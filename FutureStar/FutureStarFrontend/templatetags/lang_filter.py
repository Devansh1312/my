from django import template

register = template.Library()
@register.simple_tag
def lang(value, current_language, field_name):
    try:
        field_name_with_lang = f"{field_name}_{current_language}"
        return getattr(value, field_name_with_lang, getattr(value, f"{field_name}_en", ""))
    except Exception as e:
        print(f"Error in language tag: {str(e)}")
        return value
