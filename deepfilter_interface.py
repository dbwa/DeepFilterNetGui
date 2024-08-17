import subprocess
import os

def process_audio(input_wav, output_dir, options={}):
    """
    Appelle DeepFilterNet pour traiter un fichier audio avec les options spécifiées.
    """
    command = [
        "deep-filter", input_wav, "-o", output_dir
    ]
    
    # Ajout des options
    if options['postfilter']:
        command += ['--pf']
    if options['pf_beta']:
        command += ['--pf-beta', str(options['pf_beta'])]
    if options['atten_lim_db']:
        command += ['--atten-lim-db', str(options['atten_lim_db'])]
    
    # Exécuter la commande
    subprocess.run(command)

    # if video_path:
    #     video = VideoFileClip(video_path)
    #     original_audio = video.audio 
    #     cleaned_audio = AudioFileClip(os.path.join(output_dir, os.path.basename(input_wav)))
        
    #     # Combiner la vidéo et le nouvel audio
    #     final_clip = video.set_audio(cleaned_audio)

    #     # Enregistrer la vidéo avec l'audio nettoyé
    #     final_clip.write_videofile(os.path.join(output_dir, os.path.basename(video_path))) 