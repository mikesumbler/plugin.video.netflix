# -*- coding: utf-8 -*-
"""
    Copyright (C) 2017 Sebastian Golasch (plugin.video.netflix)
    Copyright (C) 2020 Stefano Gottardo (original implementation module)
    Navigation handler for keyboard shortcut keys

    SPDX-License-Identifier: MIT
    See LICENSES/MIT.md for more information.
"""
from __future__ import absolute_import, division, unicode_literals

from functools import wraps

import xbmc

from resources.lib import common
from resources.lib.globals import G
from resources.lib.kodi import ui
from resources.lib.kodi.library import get_library_cls
from resources.lib.utils.logging import LOG
import resources.lib.kodi.library_utils as lib_utils


def allow_execution_decorator(check_addon=True, check_lib=False, inject_videoid=False):
    def allow_execution(func):
        """Decorator that catch exceptions"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            if check_addon and not _is_addon_opened():
                return
            if check_lib and not _is_library_ops_allowed():
                return
            if inject_videoid:
                videoid = _get_selected_videoid()
                if not videoid:
                    return
                kwargs['videoid'] = videoid
            func(*args, **kwargs)
        return wrapper
    return allow_execution


class KeymapsActionExecutor(object):
    """Executes keyboard actions"""

    def __init__(self, params):
        LOG.debug('Initializing "KeymapsActionExecutor" with params: {}', params)
        self.params = params

    @allow_execution_decorator(check_lib=True, inject_videoid=True)
    def lib_export(self, pathitems, videoid=None):  # pylint: disable=unused-argument
        """Export or update an item to the Kodi library"""
        if lib_utils.is_videoid_in_db(videoid):
            get_library_cls().update_library(videoid)
        else:
            get_library_cls().export_to_library(videoid)
        common.container_refresh()

    @allow_execution_decorator(check_lib=True, inject_videoid=True)
    def lib_remove(self, pathitems, videoid=None):  # pylint: disable=unused-argument
        """Remove an item to the Kodi library"""
        if not ui.ask_for_confirmation(common.get_local_string(30030),
                                       common.get_local_string(30124)):
            return
        get_library_cls().remove_from_library(videoid)
        common.container_refresh(use_delay=True)


def _get_selected_videoid():
    """Return the videoid from the current selected ListItem"""
    videoid_str = xbmc.getInfoLabel('ListItem.Property(nf_videoid)')
    if not videoid_str:
        return None
    return common.VideoId.from_path(videoid_str.split('/'))


def _is_library_ops_allowed():
    """Check if library operations are allowed"""
    allow_lib_operations = True
    lib_auto_upd_mode = G.ADDON.getSettingInt('lib_auto_upd_mode')
    if lib_auto_upd_mode == 0:
        return False
    is_lib_sync_with_mylist = (G.ADDON.getSettingBool('lib_sync_mylist') and
                               lib_auto_upd_mode == 2)
    if is_lib_sync_with_mylist:
        # If the synchronization of Netflix "My List" with the Kodi library is enabled
        # only in the chosen profile allow to do operations in the Kodi library otherwise
        # it creates inconsistency to the exported elements and increases the work for sync
        sync_mylist_profile_guid = G.SHARED_DB.get_value('sync_mylist_profile_guid',
                                                         G.LOCAL_DB.get_guid_owner_profile())
        allow_lib_operations = sync_mylist_profile_guid == G.LOCAL_DB.get_active_profile_guid()
    return allow_lib_operations


def _is_addon_opened():
    """Check if the add-on is opened on screen"""
    return xbmc.getInfoLabel('Container.PluginName') == G.ADDON.getAddonInfo('id')
