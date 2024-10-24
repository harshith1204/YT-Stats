from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os
from werkzeug.utils import secure_filename
import traceback  # To log the full error stack trace
from channel import get_channel_stats, generate_excel_output

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Route to serve the index.html page
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/youtube-stats', methods=['POST'])
def youtube_stats():
    try:
        # Ensure the uploaded file exists
        if 'channel_ids_file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        # Get the uploaded file
        file = request.files['channel_ids_file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # Secure the filename and save it
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Read the contents of the uploaded file (channel IDs)
        with open(file_path, 'r') as f:
            channel_ids = [line.strip() for line in f.readlines()]

        # Get other form data
        start_datetime_str = request.form.get('start_datetime')
        end_datetime_str = request.form.get('end_datetime')

        # Convert strings to datetime objects
        start_datetime = datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
        end_datetime = datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")

        # Call the function to get YouTube statistics and generate Excel output
        current_utc_time = datetime.utcnow()
        current_ist_time = current_utc_time + timedelta(hours=5, minutes=30)
        extraction_time_ist = current_ist_time.strftime("%Y-%m-%d %H:%M:%S")

        # Fetch channel statistics
        channel_statistics = get_channel_stats(channel_ids, start_datetime, end_datetime)
        
        # Generate the Excel file with the statistics
        output_file = generate_excel_output(channel_statistics, extraction_time_ist)
        
        return jsonify({"message": "YouTube stats processed successfully", "output_file": output_file}), 200

    except Exception as e:
        # Print the full stack trace for debugging in the console
        traceback.print_exc()

        # Return a more detailed error message in the JSON response for now
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)
