import qrcode
from io import BytesIO

class QRCodeGenerator:
    def __init__(
        self,
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    ):
        self.version = version
        self.error_correction = error_correction
        self.box_size = box_size
        self.border = border

    def create(self, data):
        qr = qrcode.QRCode(
            version=self.version,
            error_correction=self.error_correction,
            box_size=self.box_size,
            border=self.border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        # Create a BytesIO object to store the PNG image
        img_bytes = BytesIO()
        img.save(img_bytes, 'PNG')
        img_bytes.seek(0)  # Reset the pointer to the beginning of the BytesIO object
        print(type(img_bytes))

        return img_bytes

# Example usage:
if __name__ == "__main__":
    qrcode_generator = QRCodeGenerator()
    qr_code_image = qrcode_generator.create("Hello, world!")
    # You can now use the qr_code_image BytesIO object as needed
    # For example, you can send it as a Telegram photo