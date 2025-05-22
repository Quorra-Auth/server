from fastapi.responses import StreamingResponse
import qrcode
import io
import urllib
from datetime import datetime, timedelta

from .keys import sign_jwt


class QRCodeResponse(StreamingResponse):
    media_type = "image/png"


def generate_qr(text: str) -> StreamingResponse:
    qr = qrcode.QRCode()
    qr.add_data(text)
    qr.make()
    img = qr.make_image()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return QRCodeResponse(buf)


def generate_id_token(sub, client_id, issuer, nonce):
    now = datetime.now()
    payload = {
        "iss": issuer,
        "sub": sub,
        "aud": client_id,
        "exp": int((now + timedelta(minutes=10)).timestamp()),
        "iat": int(now.timestamp()),
        "nonce": nonce,
    }
    return sign_jwt(payload)


def url_encoder(path, **params):
    parsed = list(urllib.parse.urlparse(path))
    parsed[4] = urllib.parse.urlencode(params)
    return urllib.parse.urlunparse(parsed)

