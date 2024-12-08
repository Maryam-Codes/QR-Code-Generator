from flask import Flask, render_template, request
import qrcode
from io import BytesIO
import base64
from PIL import Image, ImageDraw
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

def add_logo_to_qr(qr_img, logo_path):
    logo = Image.open(logo_path)
    qr_width, qr_height = qr_img.size

    logo_size = int(qr_width * 0.25)
    logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

    pos = ((qr_width - logo_size) // 2, (qr_height - logo_size) // 2)
    qr_img.paste(logo, pos, logo.convert("RGBA"))
    return qr_img


def apply_shape_to_qr(img, shape):
    img = img.convert("RGBA")
    width, height = img.size
    mask = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(mask)

    if shape == 'circle':
        draw.ellipse((0, 0, width, height), fill=255)
    elif shape == 'triangle':
        draw.polygon([(width / 2, 0), (0, height), (width, height)], fill=255)
    elif shape == 'square':
        draw.rectangle((0, 0, width, height), fill=255)
    elif shape == 'star':
        # Draw a star (five-pointed)
        points = [
            (width * 0.5, height * 0.05),
            (width * 0.61, height * 0.35),
            (width * 0.98, height * 0.35),
            (width * 0.68, height * 0.58),
            (width * 0.79, height * 0.91),
            (width * 0.5, height * 0.7),
            (width * 0.21, height * 0.91),
            (width * 0.32, height * 0.58),
            (width * 0.02, height * 0.35),
            (width * 0.39, height * 0.35),
        ]
        draw.polygon(points, fill=255)
   
    img.putalpha(mask)
    return img



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    data = request.form['text']
    size = int(request.form['size'])
    foreground_color = request.form['foreground_color']
    background_color = request.form['background_color']
    img_format = request.form['format']
    shape = request.form['shape']
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color=foreground_color, back_color=background_color).convert('RGB')
    
    img = apply_shape_to_qr(img, shape)
    
    if 'logo' in request.files:
        logo_file = request.files['logo']
        if logo_file.filename != '':
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_file.filename)
            logo_file.save(logo_path)
            img = add_logo_to_qr(img, logo_path)

    buffered = BytesIO()
    img.save(buffered, format=img_format)
    img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return render_template('index.html', img_base64=img_base64)

if __name__ == '__main__':
    app.run(debug=True)
