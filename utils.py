import os
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip
import wave
import numpy as np
import matplotlib.pyplot as plt

def get_audio_metadata(file_path):
    audio = AudioSegment.from_file(file_path)
    channels = audio.channels
    sample_width = audio.sample_width
    frame_rate = audio.frame_rate
    duration = len(audio) / 1000.0  # en secondes
    return(channels,sample_width, frame_rate,duration)
    
def convert_to_wav(file_path, temp_dir='temp', output_format='wav'):
    output_wav = os.path.join(temp_dir, os.path.basename(file_path).replace(os.path.splitext(file_path)[1], f".{output_format}"))
    
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    audio = AudioSegment.from_file(file_path)
    audio = audio.set_frame_rate(48000).set_channels(1)
    audio.export(output_wav, format=output_format)
    
    return output_wav

def reconstruct_video_from_audio_and_video(video_file_path, audio_file_path, output_file_path):
    # refabrique la vidéo à partir de l'ancienne piste vidéo et de la nouvelle piste audio de
    video = VideoFileClip(video_file_path)
    original_audio = video.audio 
    cleaned_audio = AudioFileClip(audio_file_path)
    
    # Combiner la vidéo et le nouvel audio
    final_clip = video.set_audio(cleaned_audio)

    # Enregistrer la vidéo avec l'audio nettoyé
    final_clip.write_videofile(output_file_path)
