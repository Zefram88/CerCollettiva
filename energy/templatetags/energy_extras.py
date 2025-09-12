from django import template

register = template.Library()


@register.filter(name="get_item")
def get_item(dictionary, key):
    """
    Filtro template per accedere ai valori di un dizionario con una chiave.
    Uso: {{ my_dict|get_item:key }}
    """
    if not dictionary:
        return None
    return dictionary.get(key)
