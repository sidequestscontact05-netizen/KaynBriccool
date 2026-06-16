from django import template
from django.utils.safestring import mark_safe

register = template.Library()

RANKS = ['Beginner', 'Explorer', 'Challenger', 'Adventurer', 'Elite', 'Legend']

CATEGORY_ICONS = {
    'administration & juridique': 'file-text',
    'aide personnelle': 'heart-handshake',
    'animaux': 'paw',
    'autres': 'dots-circle-horizontal',
    'beauté & bien-être': 'sparkles',
    'bricolage & jardinage': 'tools',
    'courses & achats': 'shopping-cart',
    'cuisine & traiteur': 'chef-hat',
    'informatique & digital': 'device-laptop',
    'livraison': 'package',
    'libvraison': 'package',
    'maintenance': 'settings',
    'ménage': 'home',
    'photo & vidéo': 'camera',
    'événementiel': 'calendar-event',
}


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def conv_id(value):
    if not value:
        return None
    if hasattr(value, 'id'):
        return value.id
    return value


@register.filter
def rank_name(level):
    try:
        idx = int(level) - 1
        if idx >= len(RANKS):
            return 'Legend'
        return RANKS[idx]
    except (ValueError, TypeError):
        return 'Beginner'


LEVEL_XP_THRESHOLDS = [0, 100, 300, 600, 1000, 1500, 2100, 2800, 3600, 4500, 5500]


@register.filter
def next_level_xp(level):
    """Return XP needed for next level threshold."""
    try:
        lv = int(level)
    except (ValueError, TypeError):
        return 100
    idx = min(lv, len(LEVEL_XP_THRESHOLDS) - 1)
    return LEVEL_XP_THRESHOLDS[idx]


@register.filter
def prev_level_xp(level):
    """Return XP threshold for current level."""
    try:
        lv = int(level)
    except (ValueError, TypeError):
        return 0
    idx = min(lv - 1, len(LEVEL_XP_THRESHOLDS) - 1)
    return LEVEL_XP_THRESHOLDS[idx]


@register.filter
def sub(value, arg):
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def stars(value):
    try:
        val = float(value)
    except (ValueError, TypeError):
        return ''
    full = int(val)
    half = 1 if val - full >= 0.5 else 0
    empty = 5 - full - half
    stars_html = ''
    for _ in range(full):
        stars_html += '<svg class="lbc-star filled" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
    for _ in range(half):
        stars_html += '<svg class="lbc-star half" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
    for _ in range(empty):
        stars_html += '<svg class="lbc-star" viewBox="0 0 24 24" fill="currentColor" stroke="none"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
    return mark_safe(stars_html)


@register.filter
def category_icon(cat):
    name = (getattr(cat, 'name', '') or '').strip().lower()
    slug = (getattr(cat, 'slug', '') or '').strip().lower()
    return CATEGORY_ICONS.get(name) or CATEGORY_ICONS.get(slug) or 'category'
