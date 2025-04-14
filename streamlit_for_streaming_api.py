# import streamlit as st
# import requests
# import time
# from threading import Thread

# # ✅ MUST be the first Streamlit command
# st.set_page_config(page_title="Live Voice Transcriber", layout="centered")

# # ✅ Title and divider
# st.markdown("<h2 style='text-align: center;'>🎙️ Live Voice Transcriber</h2>", unsafe_allow_html=True)
# st.markdown("---")

# # ✅ Session state setup
# if "is_recording" not in st.session_state:
#     st.session_state.is_recording = False
# if "transcription" not in st.session_state:
#     st.session_state.transcription = ""
# if "stream_container" not in st.session_state:
#     st.session_state.stream_container = st.empty()
# if "stream_thread" not in st.session_state:
#     st.session_state.stream_thread = None

# # ✅ Backend endpoints
# START_URL = "http://127.0.0.1:5000/transcribe"
# STOP_URL = "http://127.0.0.1:5000/transcription_result"

# # ✅ Transcription streaming function
# def stream_transcription():
#     with requests.post(START_URL, stream=True) as response:
#         if response.status_code == 200:
#             for line in response.iter_lines():
#                 if line:
#                     decoded = line.decode().replace("data: ", "")
#                     st.session_state.transcription += decoded + " "
#                     st.session_state.stream_container.markdown(f"**Live:** {st.session_state.transcription}")
#                     if not st.session_state.is_recording:
#                         break
#                     time.sleep(6)

# # ✅ Toggle recording button
# if st.button("🎤 Start Recording" if not st.session_state.is_recording else "🛑 Stop Recording"):
#     if not st.session_state.is_recording:
#         # Start recording
#         st.session_state.is_recording = True
#         st.session_state.transcription = ""
#         st.session_state.stream_container = st.empty()

#         # Start background thread
#         st.session_state.stream_thread = Thread(target=stream_transcription)
#         st.session_state.stream_thread.start()
#     else:
#         # Stop recording
#         st.session_state.is_recording = False

#         # Wait for the thread to finish
#         if st.session_state.stream_thread:
#             st.session_state.stream_thread.join()

#         # Get full result
#         try:
#             response = requests.get(STOP_URL)
#             if response.status_code == 200:
#                 result = response.json().get("transcription", "")
#                 st.session_state.transcription = result
#         except Exception as e:
#             st.session_state.transcription = f"Error retrieving transcription: {str(e)}"

# # ✅ Show transcription result
# if not st.session_state.is_recording and st.session_state.transcription:
#     st.markdown("### 📜 Complete Transcription")
#     st.success(st.session_state.transcription)




import streamlit as st
import requests

# Set Streamlit page config at the top
st.set_page_config(page_title="Live Voice Transcriber", layout="centered")

# Initialize session state variables
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = ""

st.title("🎙️ Live Voice Transcriber")
st.markdown("Click the button below to start or stop recording. Final transcription will appear below.")

# Toggle function
def toggle_recording():
    if not st.session_state.is_recording:
        # Start recording
        st.session_state.is_recording = True
        st.session_state.transcribed_text = ""

        # Start recording in the background
        try:
            requests.post("http://localhost:5000/transcribe")
        except Exception as e:
            st.error(f"Failed to start recording: {str(e)}")
    else:
        # Stop recording
        st.session_state.is_recording = False

        with st.spinner("Finalizing transcription..."):
            try:
                result = requests.get("http://localhost:5000/transcription_result")
                if result.status_code == 200:
                    st.session_state.transcribed_text = result.json().get("transcription", "")
                else:
                    st.error("Error fetching transcription result.")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Display button with label
button_label = "🟢 Start Recording" if not st.session_state.is_recording else "🔴 Stop Recording"
if st.button(button_label):
    toggle_recording()

# Show final transcription after stopping
if st.session_state.transcribed_text and not st.session_state.is_recording:
    st.subheader("📝 Final Transcription:")
    st.write(st.session_state.transcribed_text)
