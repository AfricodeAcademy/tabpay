from rembg import remove
from PIL import Image
import io

# Load your image (make sure to adjust the path as needed)
with open("/home/captain/Africode/tabpay/app/static/images/logo.png", "rb") as image_file:
    input_data = image_file.read()

# Remove the background
output_data = remove(input_data)

# Save the image with no background
with open("/home/captain/Africode/tabpay/app/static/images/TabPay_logo.png", "wb") as output_image:
    output_image.write(output_data)

# Optionally display the output image
img = Image.open(io.BytesIO(output_data))
img.show()
