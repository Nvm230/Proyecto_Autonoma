import speech_recognition as sr
import sys

def main():
    print("=== TEST DE LÓGICA DE VOZ (COMO EN ROS 2) ===")
    
    # 1. Buscar el dispositivo "pulse" automáticamente
    device_index = None
    mics = sr.Microphone.list_microphone_names()
    print(f"\nDispositivos disponibles ({len(mics)}):")
    for i, name in enumerate(mics):
        print(f"  [{i}] {name}")
        if name.lower() == 'pulse' and device_index is None:
            device_index = i

    if device_index is not None:
        print(f"\n=> AUTO-SELECCIONADO: Dispositivo 'pulse' (Index {device_index})")
    else:
        print("\n=> ADVERTENCIA: No se encontró 'pulse'. Usando el micrófono por defecto.")

    recognizer = sr.Recognizer()
    
    # 2. Inicializar micrófono y calibrar
    try:
        microphone = sr.Microphone(device_index=device_index)
        mic_source = microphone.__enter__()  # Abrimos permanentemente
        
        print("\n[INFO] Calibrando ruido de fondo... (silencio por 2 segundos)")
        recognizer.adjust_for_ambient_noise(mic_source, duration=2.0)
        recognizer.pause_threshold = 0.8
            
        print("\n[INFO] Micrófono listo. Empieza la prueba.")
    except Exception as e:
        print(f"\n[ERROR FATAL] No se pudo abrir el micrófono: {e}")
        sys.exit(1)

    # 3. Escuchar (igual que en el timer_callback de ROS 2)
    print("\n[INFO] Escuchando un comando... (Di 'buscar botella' fuerte y claro)")
    try:
        audio = recognizer.listen(mic_source, timeout=2.0, phrase_time_limit=5.0)
            
        print(f"[INFO] Audio capturado exitosamente ({len(audio.frame_data)} bytes). Enviando a Google Speech API...")
        
        import urllib.request
        import socket
        socket.setdefaulttimeout(5.0)  # ¡EVITAR QUE SE CUELGUE PARA SIEMPRE!
        
        try:
            print("[INFO] Comprobando conexión HTTPS a la API de Google...")
            # Esta es la URL exacta que usa la librería por debajo
            urllib.request.urlopen('https://www.google.com/speech-api/v2/recognize?output=json&lang=es-ES&key=ABC', timeout=5.0)
        except urllib.error.HTTPError as e:
            # Un error 403 o 400 es BUENO, significa que el servidor respondió y no se colgó.
            print(f"[INFO] Conexión HTTPS OK (Google respondió con código {e.code}). Subiendo audio...")
        except Exception as e:
            print(f"[ERROR FATAL] La conexión segura a la API de Google falla o se cuelga: {e}")
            sys.exit(1)
            
        # 4. Reconocer
        command = recognizer.recognize_google(audio, language="es-ES")
        print(f"\n[ÉXITO] ==> COMANDO RECONOCIDO: '{command.upper()}' <==")
        
    except sr.WaitTimeoutError:
        print("\n[ERROR] Timeout. No detecté ninguna voz (¿el micro está mudo o hablaste muy suave?).")
    except sr.UnknownValueError:
        print("\n[ERROR] Google recibió el audio pero no pudo entender ninguna palabra.")
        print("        (Puede ser estática, ruido puro, o volumen extremadamente bajo).")
    except sr.RequestError as e:
        print(f"\n[ERROR] Falló la conexión con Google Speech API: {e}")
    except Exception as e:
        print(f"\n[ERROR INESPERADO]: {e}")

if __name__ == '__main__':
    main()
