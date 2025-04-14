import os
import tempfile
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, jsonify, Response

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Audio settings
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5

complete_dialogue_transcribe = ""
stop_transcription = False

def record_and_stream_transcription():
    global complete_dialogue_transcribe

    try:
        while not stop_transcription:
            print("Recording...")
            recording = sd.rec(
                int(RECORD_SECONDS * RATE),
                samplerate=RATE,
                channels=CHANNELS,
                dtype='int16'
            )
            sd.wait()  # Wait until recording is finished

            if stop_transcription:
                break

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                wav.write(temp_audio.name, RATE, recording)

            try:
                with open(temp_audio.name, "rb") as f:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f
                    )
                    text = transcript.text.strip()
                    print("Transcript:", text)
                    complete_dialogue_transcribe += text + " "
                    yield f"data: {text}\n\n"
            except Exception as e:
                yield f"data: Error during transcription: {str(e)}\n\n"
            finally:
                os.remove(temp_audio.name)

    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"
    finally:
        print("Transcription stopped.")


app = Flask(__name__)

@app.route('/transcribe', methods=['POST'])
def start_transcription():
    global stop_transcription, complete_dialogue_transcribe
    complete_dialogue_transcribe = ""
    stop_transcription = False
    return Response(record_and_stream_transcription(), content_type='text/event-stream')

@app.route('/transcription_result', methods=['GET'])
def get_transcription_result():
    global complete_dialogue_transcribe, stop_transcription
    stop_transcription = True
    return jsonify({"transcription": complete_dialogue_transcribe.strip()}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
