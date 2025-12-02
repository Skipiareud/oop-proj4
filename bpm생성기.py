import librosa
y, sr = librosa.load("virus.wav")
tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
print(tempo)