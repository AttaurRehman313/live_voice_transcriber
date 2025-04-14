import os
import wave
import pyaudio
import tempfile
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask, jsonify, Response

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Audio settings
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5

complete_dialogue_transcribe = ""
stop_transcription = False

def record_and_stream_transcription():
    local_audio = pyaudio.PyAudio()

    # Optional: list input devices
    print("Available Audio Input Devices:")
    for i in range(local_audio.get_device_count()):
        info = local_audio.get_device_info_by_index(i)
        if info["maxInputChannels"] > 0:
            print(f"Device {i}: {info['name']}")

    # Try to open microphone stream
    try:
        stream = local_audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
    except OSError as e:
        yield f"data: Failed to open audio stream: {str(e)}\n\n"
        local_audio.terminate()
        return

    try:
        while not stop_transcription:
            frames = []
            for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                if stop_transcription:
                    break
                data = stream.read(CHUNK)
                frames.append(data)

            if stop_transcription:
                break

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                wf = wave.open(temp_audio.name, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(local_audio.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                wf.close()

            try:
                with open(temp_audio.name, "rb") as f:
                    transcript = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=f
                    )
                    text = transcript.text.strip()
                    print("Transcript:", text)
                    global complete_dialogue_transcribe
                    complete_dialogue_transcribe += text + " "
                    yield f"data: {text}\n\n"
            except Exception as e:
                yield f"data: Error during transcription: {str(e)}\n\n"
            finally:
                os.remove(temp_audio.name)

    except Exception as e:
        yield f"data: Error: {str(e)}\n\n"
    finally:
        stream.stop_stream()
        stream.close()
        local_audio.terminate()
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
