from itertools import groupby
import sublime

SETTINGS = "tabs_extra.sublime-settings"


def numeric_sort(text):
    if sublime.load_settings(SETTINGS).get("numeric_sort", False):
        final_text = []
        for digit, g in groupby(text, lambda x: x.isdigit()):
            val = "".join(g)
            if digit:
                final_text.append(int(val))
            else:
                final_text.append(val)
    else:
        final_text = text
    return final_text
