# Copyright 2021-2022 Mufeed Ali
# Copyright 2021-2022 Rafael Mardojai CM
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, GLib, GObject

from dialect.define import APP_ID
from dialect.providers import (
    check_translator_availability,
    get_fallback_translator_name,
    TRANSLATORS,
    TTS
)


class Settings(Gio.Settings):
    """
    Dialect settings handler
    """
    __gsignals__ = {
        'provider-changed': (GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, (str, str))
    }

    instance = None
    providers = {}

    def __init__(self, *args):
        super().__init__(*args)

    @staticmethod
    def new():
        """Create a new instance of Settings."""
        g_settings = Settings(APP_ID)
        g_settings.init_translators_settings()
        return g_settings

    @staticmethod
    def get():
        """Return an active instance of Settings."""
        if Settings.instance is None:
            Settings.instance = Settings.new()
        return Settings.instance

    def init_translators_settings(self):
        """Initialize translators settings with its default values."""
        self.translators_list = list(TRANSLATORS.keys())
        for name, instance in TRANSLATORS.items():
            settings = self.get_translator_settings(name)
            if not settings.get_boolean('init'):
                settings.set_strv('src-langs', instance.defaults['src_langs'])
                settings.set_strv('dest-langs', instance.defaults['dest_langs'])
                settings.set_string('instance-url', instance.defaults['instance_url'])
                settings.set_string('api-key', instance.defaults['api_key'])
                settings.set_boolean('init', True)

    @property
    def translators_list(self):
        return self.get_child('translators').get_strv('list')

    @translators_list.setter
    def translators_list(self, translators):
        self.get_child('translators').set_strv('list', translators)

    @property
    def active_translator(self):
        value = self.get_child('translators').get_string('active')

        if check_translator_availability(value):
            return value

        self.active_translator = get_fallback_translator_name()
        return get_fallback_translator_name()

    @active_translator.setter
    def active_translator(self, translator):
        self.get_child('translators').set_string('active', translator)

    def get_translator_settings(self, translator=None):
        def on_changed(_settings, key, name):
            self.emit('provider-changed', name, key)

        def get_settings(name):
            path = self.get_child('translators').get_property('path')
            if not path.endswith('/'):
                path += '/'
            path += name + '/'

            settings = ProviderSettings(APP_ID + '.translator', path)
            settings.connect('changed', on_changed, name)
            return settings

        if translator is None:
            translator = self.active_translator

        if translator in self.providers:
            return self.providers[translator]

        self.providers[translator] = get_settings(translator)
        return self.providers[translator]

    @property
    def src_langs(self):
        return self.get_translator_settings().get_strv('src-langs')

    @src_langs.setter
    def src_langs(self, src_langs):
        self.get_translator_settings().set_strv('src-langs', src_langs)

    def reset_src_langs(self):
        self.src_langs = TRANSLATORS[self.active_translator].defaults['src_langs']

    @property
    def dest_langs(self):
        return self.get_translator_settings().get_strv('dest-langs')

    @dest_langs.setter
    def dest_langs(self, dest_langs):
        self.get_translator_settings().set_strv('dest-langs', dest_langs)

    def reset_dest_langs(self):
        self.dest_langs = TRANSLATORS[self.active_translator].defaults['dest_langs']

    @property
    def instance_url(self):
        return self.get_translator_settings().get_string('instance-url')

    @instance_url.setter
    def instance_url(self, url):
        self.get_translator_settings().set_string('instance-url', url)

    def reset_instance_url(self):
        self.instance_url = TRANSLATORS[self.active_translator].defaults['instance_url']

    @property
    def api_key(self):
        return self.get_translator_settings().get_string('api-key')

    @api_key.setter
    def api_key(self, api_key):
        self.get_translator_settings().set_string('api-key', api_key)

    def reset_api_key(self):
        self.api_key = TRANSLATORS[self.active_translator].defaults['api_key']

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
    def active_tts(self):
        """Return the user's preferred TTS service."""
        value = self.get_child('tts').get_string('active')

        if value != '' and value not in TTS.keys():
            value = ''
            self.active_tts = value

        return value

    @active_tts.setter
    def active_tts(self, tts):
        """Set the user's preferred TTS service."""
        self.get_child('tts').set_string('active', tts)

    @property
    def color_scheme(self):
        return self.get_string('color-scheme')

    @color_scheme.setter
    def color_scheme(self, scheme):
        self.set_string('dark-mode', scheme)

    @property
    def live_translation(self):
        return self.get_boolean('live-translation')

    @live_translation.setter
    def live_translation(self, state):
        self.set_boolean('live-translation', state)

    @property
    def sp_translation(self):
        return self.get_boolean('sp-translation')

    @sp_translation.setter
    def sp_translation(self, state):
        self.set_boolean('sp-translation', state)

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


class ProviderSettings(Gio.Settings):
    """
    Dialect provider settings handler
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def instance_url(self):
        return self.get_string('instance-url')

    @instance_url.setter
    def instance_url(self, url):
        self.set_string('instance-url', url)

    @property
    def api_key(self):
        return self.get_string('api-key')

    @api_key.setter
    def api_key(self, api_key):
        self.set_string('api-key', api_key)
