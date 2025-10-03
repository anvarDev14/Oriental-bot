"""Inline keyboards"""
from .fakultet import faculty_menu, FACULTY_MAPPING
from .support import get_support_keyboard
from .admin_actions import get_admin_fakultet_keyboard, get_confirm_keyboard

__all__ = [
    'faculty_menu',
    'FACULTY_MAPPING',
    'get_support_keyboard',
    'get_admin_fakultet_keyboard',
    'get_confirm_keyboard'
]