# Copyright 2021 Mufeed Ali
# Copyright 2021 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

import json

from gi.repository import Gio, GLib

from dialect.define import APP_ID
from dialect.translators import (
    check_backend_availability,
    get_fallback_backend_name,
    TRANSLATORS
)
from dialect.tts import TTS


class Settings(Gio.Settings):
    """
    Dialect settings handler
    """

    instance = None
    translator = None

    def __init__(self):
        Gio.Settings.__init__(self)
        self.init_translators_settings()
        self.migrate_legacy()

    @staticmethod
    def new():
        """Create a new instance of Settings."""
        g_settings = Gio.Settings.new(APP_ID)
        g_settings.__class__ = Settings
        return g_settings

    @staticmethod
    def get():
        """Return an active instance of Settings."""
        if Settings.instance is None:
            Settings.instance = Settings.new()

        return Settings.instance

    def init_translators_settings(self):
        """Intialize translators settings with its default values."""
        self.translators_list = list(TRANSLATORS.keys())
        for name, instance in TRANSLATORS.items():
            settings = self.get_translator_settings(name)
            if not settings.get_boolean('init'):
                settings.set_strv('src-langs', instance.src_langs)
                settings.set_strv('dest-langs', instance.dest_langs)
                settings.set_string('instance-url', instance.instance_url)
                settings.set_string('api-key', instance.api_key)
                settings.set_boolean('init', True)

    @property
    def translators_list(self):
        return self.get_child('translators').get_strv('list')

    @translators_list.setter
    def translators_list(self, translators):
        self.get_child('translators').set_strv('list', translators)

    @property
    def active_translator(self):
        return self.get_child('translators').get_string('active')

    @active_translator.setter
    def active_translator(self, translator):
        self.get_child('translators').set_string('active', translator)
        self.translator = None

    def get_translator_settings(self, translator=None):
        def get_settings(name):
            path = self.get_child('translators').get_property('path')
            if not path.endswith('/'):
                path += '/'
            path += name + '/'
            return Gio.Settings(APP_ID + '.translator', path)

        if translator is not None:
            translator = get_settings(translator)
            return translator
        if self.translator is None:
            self.translator = get_settings(self.active_translator)
            self.translator.delay()
        return self.translator

    def save_translator_settings(self):
        if self.translator is not None:
            self.translator.apply()

    @property
    def src_langs(self):
        return self.get_translator_settings().get_strv('src-langs')

    @src_langs.setter
    def src_langs(self, src_langs):
        self.get_translator_settings().set_strv('src-langs', src_langs)

    @property
    def dest_langs(self):
        return self.get_translator_settings().get_strv('dest-langs')

    @dest_langs.setter
    def dest_langs(self, dest_langs):
        self.get_translator_settings().set_strv('dest-langs', dest_langs)

    @property
    def instance_url(self):
        return self.get_translator_settings().get_string('instance-url')

    @instance_url.setter
    def instance_url(self, url):
        self.get_translator_settings().set_string('instance-url', url)
        self.save_translator_settings()

    @property
    def api_key(self):
        return self.get_translator_settings().get_string('api-key')

    @api_key.setter
    def api_key(self, api_key):
        self.get_translator_settings().set_string('api-key', api_key)
        self.save_translator_settings()

    @property
    def window_size(self):
        value = self.get_value('window-size')
        return (value[0], value[1])

    @window_size.setter
    def window_size(self, size):
        width, height = size
        self.set_value('window-size', GLib.Variant('ai', [width, height]))

    @property
    def translate_accel(self):
        """Return the user's preferred translation shortcut."""
        value = self.translate_accel_value

        if value == 0:
            return '<Primary>Return'
        if value == 1:
            return 'Return'

        return '<Primary>Return'

    @property
    def translate_accel_value(self):
        """Return the user's preferred translation shortcut value."""
        return self.get_int('translate-accel')

    @property
    def tts(self):
        """Return the user's preferred TTS service."""
        value = self.get_string('tts-name')
        if value not in TTS.keys():
            value = ''
            self.tts = value
        return value

    @tts.setter
    def tts(self, value):
        """Set the user's preferred TTS service."""
        self.set_string('tts-name', value)

    @property
    def dark_mode(self):
        return self.get_boolean('dark-mode')

    @dark_mode.setter
    def dark_mode(self, state):
        self.set_boolean('dark-mode', state)

    @property
    def live_translation(self):
        return self.get_boolean('live-translation')

    @live_translation.setter
    def live_translation(self, state):
        self.set_boolean('live-translation', state)

    @property
    def show_pronunciation(self):
        return self.get_boolean('show-pronunciation')

    @property
    def show_pronunciation_value(self):
        return self.get_value('show-pronunciation')

    @show_pronunciation.setter
    def show_pronunciation(self, state):
        self.set_boolean('show-pronunciation', state)

    @property
    def src_auto(self):
        return self.get_boolean('src-auto')

    @src_auto.setter
    def src_auto(self, state):
        self.set_boolean('src-auto', state)

    def migrate_legacy(self):
        pass

    @property
    def backend(self):
        """Return the user's preferred backend."""
        # Dialect 1.2.0 and below used the backend key and
        # stored the index of the chosen backend as an int.
        value = self.get_int('backend')

        if value == -1:
            value = self.get_string('backend-name')
        else:
            if value == 0:
                value = 'google'
            elif value == 1:
                value = 'libretranslate'

        if check_backend_availability(value):
            return value

        self.backend = get_fallback_backend_name()
        return get_fallback_backend_name()

    @backend.setter
    def backend(self, name):
        """
        Set the user's preferred backend.

        :param name: name of backend
        :type name: string
        """
        self._delete_int_key('backend')  # Set deprecated key to unused state.
        self.set_string('backend-name', name)

    def get_instance_url(self, backend):
        # Dialect 1.2.0 and below used separate keys for each
        # backend-specific setting.
        instance_url = self.get_string(f'{backend}-instance')
        if instance_url:
            return instance_url

        settings = self.backend_settings.get(backend)

        if settings is not None and settings.get('instance-url'):
            return settings.get('instance-url')

        return TRANSLATORS[backend].instance_url

    def set_instance_url(self, backend, instance_url):
        self._delete_str_key(f'{backend}-instance')  # Set deprecated key to unused state.
        self._set_backend_setting(backend, 'instance-url', instance_url)

    def reset_instance_url(self, backend):
        self._delete_str_key(f'{backend}-instance')  # Set deprecated key to unused state.
        self.instance_url = TRANSLATORS[self.active_translator].instance_url

    def get_dest_langs(self, backend):
        # Dialect 1.2.0 and below used separate keys for each
        # backend-specific setting.
        dest_langs = list(self.get_value(f'{backend}-dest-langs'))
        if dest_langs:
            return dest_langs

        settings = self.backend_settings.get(backend)

        if settings is not None and settings.get('dest-langs'):
            return settings.get('dest-langs')

        return TRANSLATORS[backend].dest_langs

    def set_dest_langs(self, backend, langs):
        self._delete_arr_key(f'{backend}-dest-langs')  # Set deprecated key to unused state.
        self._set_backend_setting(backend, 'dest-langs', langs)

    def reset_dest_langs(self, backend):
        self._delete_arr_key(f'{backend}-dest-langs')  # Set deprecated key to unused state.
        self.dest_langs = TRANSLATORS[backend].dest_langs

    def get_src_langs(self, backend):
        # Dialect 1.2.0 and below used separate keys for each
        # backend-specific setting.
        src_langs = list(self.get_value(f'{backend}-src-langs'))
        if src_langs:
            return src_langs

        settings = self.backend_settings.get(backend)

        if settings is not None and settings.get('src-langs'):
            return settings.get('src-langs')

        return TRANSLATORS[backend].src_langs

    def set_src_langs(self, backend, langs):
        self._delete_arr_key(f'{backend}-src-langs')  # Set deprecated key to unused state.
        self._set_backend_setting(backend, 'src-langs', langs)

    def reset_src_langs(self, backend):
        self._delete_arr_key(f'{backend}-src-langs')  # Set deprecated key to unused state.
        self.src_langs = TRANSLATORS[backend].src_langs

    @property
    def backend_settings(self):
        return json.loads(self.get_string('backend-settings'))

    @backend_settings.setter
    def backend_settings(self, value):
        self.set_string('backend-settings', json.dumps(value))

    def _set_backend_setting(self, backend, key, value):
        """
        Sets the backend settings with key and value.
        """
        settings = self.backend_settings

        if backend not in settings:
            settings[backend] = {}

        settings[backend][key] = value
        self.backend_settings = settings

    def _delete_arr_key(self, key):
        val = self.get_strv(key)
        if val != []:
            self.set_value(key, GLib.Variant('as', []))

    def _delete_enum_key(self, key):
        val = self.get_enum(key)
        if val > -1:
            self.set_enum(key, -1)

    def _delete_int_key(self, key):
        val = self.get_int(key)
        if val > -1:
            self.set_int(key, -1)

    def _delete_str_key(self, key):
        val = self.get_string(key)
        if val != '':
            self.set_value(
                key,
                GLib.Variant('s', '')
            )
