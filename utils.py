import os
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip
import numpy as np

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

def convert_audio_format(input_file, output_file, format='wav'):
    """
    Convertit un fichier audio dans le format désiré
    """
    try:
        print(f"[DEBUG] Conversion audio: {input_file} -> {output_file} ({format})")
        audio = AudioSegment.from_file(input_file)
        audio.export(output_file, format=format)
        print("[DEBUG] Conversion audio terminée")
    except Exception as e:
        print(f"[ERROR] Erreur lors de la conversion audio: {str(e)}")
        raise

def reconstruct_video_from_audio_and_video(video_file_path, audio_file_path, output_file_path, format='mp4'):
    """
    Reconstruit une vidéo en combinant la piste vidéo originale avec le nouvel audio
    """
    try:
        print(f"[DEBUG] Reconstruction vidéo: début")
        print(f"[DEBUG] Format de sortie: {format}")
        
        video = VideoFileClip(video_file_path)
        cleaned_audio = AudioFileClip(audio_file_path)
        
        # Combiner la vidéo et le nouvel audio
        final_clip = video.set_audio(cleaned_audio)
        
        # Paramètres selon le format
        if format == 'mp4':
            codec = 'libx264'
            audio_codec = 'aac'
        elif format == 'mkv':
            codec = 'libx264'
            audio_codec = 'libvorbis'
        elif format == 'avi':
            codec = 'mpeg4'
            audio_codec = 'mp3'
        else:  # mov ou autres
            codec = 'libx264'
            audio_codec = 'aac'
        
        # Enregistrer la vidéo
        final_clip.write_videofile(
            output_file_path,
            codec=codec,
            audio_codec=audio_codec,
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Nettoyage
        video.close()
        cleaned_audio.close()
        
        print(f"[DEBUG] Reconstruction vidéo: terminée")
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de la reconstruction vidéo: {str(e)}")
        raise