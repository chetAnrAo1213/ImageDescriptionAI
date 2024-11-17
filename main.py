from flask import Flask, render_template, request
from pathlib import Path
import google.generativeai as genai
import os

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

genai.configure(api_key="AIzaSyAlKyF3PpDiNc4KUAr7uKDA-v7HtDQcpDA")

def image_format(image_path):
    img = Path(image_path)

    if not img.exists():
        raise FileNotFoundError(f"Could not find image: {img}")

    if img.suffix in ['.jpeg', '.jpg']:
        mime_type = "image/jpeg"
    elif img.suffix == '.png':
        mime_type = "image/png"
    else:
        raise ValueError("Unsupported image format. Only JPEG and PNG are allowed.")

    return [{"mime_type": mime_type, "data": img.read_bytes()}]

def gemini_output(image_path, system_prompt, user_prompt):
    try:
        image_info = image_format(image_path)
        input_prompt = [system_prompt, image_info[0], user_prompt]

        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(input_prompt)
        response_text = response.text

        formatted_response = (
            response_text.replace("##", "<h6><br>")
            .replace("* ", "<li>")
            .replace(" - ", "</li><li>")
            .replace("**", "</h6>")
        )
        return f"<ul>{formatted_response}</ul>"
    except Exception as e:
        print(f"Error generating response: {e}")
        return "Error generating response"

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

system_instruction = (
    "You are an expert Feature Extractor and Image Analyzer. "
    "You should only give details as a List with a single Description. "
    "You should not respond if you can't read the file and "
    "should say 'couldn't extract details'. Output should be in a list format."
)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('image')
        if not file or file.filename == '':
            return 'No selected file'

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        user_prompt = "Extract all relevant information from the image."
        output = gemini_output(file_path, system_prompt=system_instruction, user_prompt=user_prompt)
        return render_template('result.html', response=output)

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5001)
