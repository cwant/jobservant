import os

try:
    # Try to find i18n module
    import i18n

    localedir = os.path.join(os.path.dirname(__file__),
                             '..', 'config', 'locales')
    i18n.load_path.append(localedir)
    i18n.set('filename_format', '{locale}.{format}')
    t = i18n.t
except ModuleNotFoundError:
    def t(key, **kwargs):
        return key
