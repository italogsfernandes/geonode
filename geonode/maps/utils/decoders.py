import base64


def decode_base64(data):
    """Decode base64, padding being optional.

    :param data: Base64 data as an ASCII byte string
    :returns: The decoded byte string.

    """
    _thumbnail_format = "png"
    _invalid_padding = data.find(";base64,")
    if _invalid_padding:
        _thumbnail_format = data[data.find("image/") + len("image/") : _invalid_padding]
        data = data[_invalid_padding + len(";base64,") :]
    missing_padding = len(data) % 4
    if missing_padding != 0:
        data += b"=" * (4 - missing_padding)
    return (base64.b64decode(data), _thumbnail_format)
