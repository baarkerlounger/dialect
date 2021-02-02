LANGUAGES = {
    "en": "ENGLISH"
}

class TranslatorBase:
    history = []
    supported_features = {
        "mistakes": False,
        "pronunciation": False,
        "voice": False,
    }

    def detect(self, src_text):
        pass

    def translate(self, src_text, src, dest):
        pass


class TranslationError(Exception):
    """Exception raised when translation fails."""

    def __init__(self, cause, message='Translation has failed'):
        self.cause = cause
        self.message = message
        super().__init__(self.message)


class Translation:
    text = None
    extra_data = {}

    def __init__(self, text, extra_data):
        self.text = text
        self.extra_data = extra_data

def get_translators():
    pass
