from fastapi.responses import StreamingResponse
import qrcode
import io
import urllib
import base64
from datetime import datetime, timedelta

from string import ascii_letters, digits

from .keys import sign_jwt


def generate_qr(text: str) -> str:
    """Generates a data:image/png;base64 string with an encoded QR PNG"""
    qr = qrcode.QRCode()
    qr.add_data(text)
    qr.make()
    img = qr.make_image()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()
    b64_image = base64.b64encode(img_bytes).decode("utf-8")
    return "data:image/png;base64,{}".format(b64_image)
    # buf.seek(0)
    # return QRCodeResponse(buf)


def generate_token(claims: dict):
    now = datetime.now()
    base: dict = {
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "iat": int(now.timestamp()),
    }
    return sign_jwt(base | claims)


def url_encoder(path, **params):
    parsed = list(urllib.parse.urlparse(path))
    parsed[4] = urllib.parse.urlencode(params)
    return urllib.parse.urlunparse(parsed)


def escape_valkey_tag(value: str):
    # Escape everything that is not "safe" in TAG values
    allowed_chars = ascii_letters + digits + "_"
    out = []
    for ch in value:
        if ch in allowed_chars:
            out.append(ch)
        else:
            out.append("\\" + ch)
    return "".join(out)
