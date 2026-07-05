import speech_recognition as sr

def test_mic():
    r = sr.Recognizer()
    print("Buscando micrófono...")
    try:
        with sr.Microphone() as source:
            print("Micrófono encontrado. Ajustando ruido de fondo por 2 segundos...")
            r.adjust_for_ambient_noise(source, duration=2)
            print("Habla ahora por 3 segundos (di algo como 'hola probando')...")
            audio = r.listen(source, timeout=3.0, phrase_time_limit=3.0)
            
            with open("test.wav", "wb") as f:
                f.write(audio.get_wav_data())
            print("Audio guardado en test.wav.")
            
            print("Intentando reconocer con Google (Español)...")
            try:
                text = r.recognize_google(audio, language="es-ES")
                print(f"Resultado: {text}")
            except sr.UnknownValueError:
                print("Error: Google escuchó algo pero no pudo entender las palabras (probablemente sea estática o ruido).")
            except sr.RequestError as e:
                print(f"Error de conexión a internet: {e}")
                
    except Exception as e:
        print(f"Error fatal con el micrófono: {e}")

if __name__ == '__main__':
    test_mic()
