from fastapi.responses import StreamingResponse
import qrcode
import io


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
