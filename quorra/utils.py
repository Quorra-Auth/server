from fastapi.responses import StreamingResponse
import qrcode
import io
import urllib
import base64
from datetime import datetime, timedelta

from .keys import sign_jwt


class QRCodeResponse(StreamingResponse):
    media_type = "image/png"


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


def generate_token(**kwargs):
    if "nonce" in kwargs and kwargs["nonce"] is None:
        del kwargs["nonce"]
    now = datetime.now()
    base: dict = {
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "iat": int(now.timestamp()),
    }
    payload: dict = {**kwargs}
    return sign_jwt(base | payload)


def url_encoder(path, **params):
    parsed = list(urllib.parse.urlparse(path))
    parsed[4] = urllib.parse.urlencode(params)
    return urllib.parse.urlunparse(parsed)

