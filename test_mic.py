import speech_recognition as sr

print("--- Microphones found ---")
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print(f"Device {index}: {name}")
print("-------------------------\n")

print("Testing default microphone...")
recognizer = sr.Recognizer()
try:
    with sr.Microphone() as source:
        print("Please say something loudly for 3 seconds...")
        recognizer.adjust_for_ambient_noise(source, duration=1.0)
        audio = recognizer.listen(source, timeout=3.0, phrase_time_limit=3.0)
        
    print("Audio captured! Trying to recognize...")
    text = recognizer.recognize_google(audio, language="es-ES")
    print(f"I heard: {text}")
except sr.WaitTimeoutError:
    print("ERROR: Timeout. I didn't hear any speech.")
except sr.UnknownValueError:
    print("ERROR: I heard noise but couldn't understand it.")
except Exception as e:
    print(f"FATAL ERROR: {e}")
