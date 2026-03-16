def highlight_changes(original, modified):
    highlighted = ""
    for orig_char, mod_char in zip(original, modified):
        if orig_char == "_":
            highlighted += f"\033[92m{mod_char}\033[0m"
        else:
            highlighted += mod_char
    return highlighted


def highlight_error(original, modified):
    highlighted = ""
    for orig_char, mod_char in zip(original, modified):
        if orig_char != mod_char:  
            highlighted += f"\033[91m{mod_char}\033[0m"
        else:
            highlighted += mod_char
    return highlighted