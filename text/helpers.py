def get_size(value):
    if isinstance(value, str):
        if value == '':
            return ''
        else:
            return int(value)
    return value