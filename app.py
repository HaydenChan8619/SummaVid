from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from transcription_service import TranscriptionService
from summarization_service import SummarizationService
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'  # Make sure this folder exists

# Create the upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

transcription_service = TranscriptionService()
summarization_service = SummarizationService()

summarization_prompt = "You will analyze a huge transcript from a video and create a summary in the form of a list useful to the audience. Include important information in the summary. Translate to English if needed."
important_dates_prompt = "You will analyze a huge transcript of a lecture and create a summary of all mentioned important dates, such as assignment, quiz, test, and final dates, in the form of a list."
meeting_prompt = "You will analyze a huge transcript from a meeting and create a summary of it. Mention all proceedings, matters and date mentioned as well as all decisions or future plans mentioned, in the form of a list."


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/run', methods=['POST'])
def run_the_thing():

    if request.form['whisper_model'] == "large":
        whisper_model = "large"
    elif request.form['language'] == "English":
        whisper_model = request.form['whisper_model']+".en"
    else:
        whisper_model = request.form['whisper_model']

    # link = request.form['link']
    video_type = request.form['video_type']
    gpt_model = request.form['gpt_model']
    api_key = request.form['api_key']

    print("Whisper Model: " + whisper_model)
    print("GPT Model: " + gpt_model)

    file = request.files.get('file')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        link = file_path

    transcript = transcription_service.transcribe(link, whisper_model, api_key)
    summary = summarization_service.summarize(
        transcript, gpt_model, api_key, summarization_prompt)

    # if (video_type == "lecture"):
    #     important_dates = summarization_service.summarize(
    #         transcript, gpt_model, api_key, important_dates_prompt)
    #     return render_template('index.html', summary=summary, important_dates=important_dates, transcript=transcript)
    # else:
    #     return render_template('index.html', summary=summary, transcript=transcript)

    match video_type:
        case "lecture":
            important_dates = summarization_service.summarize(
                transcript, gpt_model, api_key, important_dates_prompt)
            return render_template('index.html', summary=summary, important_dates=important_dates, transcript=transcript)
        case "meeting":
            meeting_points = summarization_service.summarize(
                transcript, gpt_model, api_key, meeting_prompt)
            return render_template('index.html', summary=summary, important_dates=meeting_points, transcript=transcript)
        case _:
            return render_template('index.html', summary=summary, transcript=transcript)


if __name__ == '__main__':
    app.run(debug=True)
