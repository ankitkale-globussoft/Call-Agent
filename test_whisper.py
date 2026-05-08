print("Importing faster_whisper...")
try:
    from faster_whisper import WhisperModel
    print("Faster Whisper imported successfully.")
except Exception as e:
    print(f"Import failed: {e}")
