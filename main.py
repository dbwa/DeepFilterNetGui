import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from deepfilter_interface import process_audio
from utils import *
import threading
import os
import pygame  # Utilisé pour le lecteur audio
import matplotlib.pyplot as plt
import tempfile 
import time
import uuid

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import librosa.display


class AudioCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DeepFilterNetGui : Nettoyage Audio/Video")
        self.root.iconbitmap("assets/icon.ico")
        self.root.geometry("800x600")
        self.root.resizable(width=False, height=False)
        self.setup_ui()


        # Initialisation du graphique pour les spectrogrammes

        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 6))
        self.fig.tight_layout(pad=0)
        self.ax1.get_xaxis().set_visible(False)
        self.ax2.get_xaxis().set_visible(False)
        self.ax1.get_yaxis().set_visible(False)
        self.ax2.get_yaxis().set_visible(False)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)  # Canvas Matplotlib
        self.canvas.get_tk_widget().pack(pady=0)

        self.temp_dir_obj=tempfile.TemporaryDirectory(suffix='_temp', prefix='deepfilternetapp_')
        self.temp_dir = self.temp_dir_obj.name 
        self.output_dir_obj=tempfile.TemporaryDirectory(suffix='_output', prefix='deepfilternetapp_')
        self.output_dir = self.output_dir_obj.name

        # Initialiser Pygame pour le lecteur audio
        pygame.mixer.init()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.duration = 1

    def setup_ui(self):
        # Bouton pour sélectionner un fichier
        button_select = tk.Button(self.root, text="Sélectionner un fichier", command=self.on_select_file)
        button_select.pack(pady=10)

        # Zone pour afficher le nom du fichier sélectionné
        self.label_file = tk.Label(self.root, text="Aucun fichier sélectionné", bg="white", width=80, height=2)
        self.label_file.pack(pady=10)

        # Zone d'information sur l'audio
        self.label_info = tk.Label(self.root, text="Aucune information sur le fichier", bg="white", width=80, height=3)
        self.label_info.pack(pady=10)

        # Zone de configuration des options
        options_frame = tk.Frame(self.root)
        options_frame.pack(pady=10)

        # Activer post-filtre
        self.postfilter_var = tk.IntVar()
        tk.Checkbutton(options_frame, text="Activer post-filtre", variable=self.postfilter_var).grid(row=0, column=0)

        # Post-filter beta
        self.pf_beta_var = tk.DoubleVar(value=0.02)
        tk.Label(options_frame, text="Post-filter Beta:").grid(row=1, column=0)
        tk.Entry(options_frame, textvariable=self.pf_beta_var).grid(row=1, column=1)

        # Atténuation limite
        self.atten_lim_db_var = tk.DoubleVar(value=100)
        tk.Label(options_frame, text="Limite d'atténuation (dB):").grid(row=2, column=0)
        tk.Entry(options_frame, textvariable=self.atten_lim_db_var).grid(row=2, column=1)

        # Spinner d'attente pendant le traitement
        self.spinner_label = tk.Label(self.root, text="", fg="red")
        self.spinner_label.pack(pady=10)

        # Bouton "Nettoyer l'audio"
        button_clean = tk.Button(self.root, text="Nettoyer l'audio", command=self.on_clean_click)
        button_clean.pack(pady=10)

       # Lecteur audio avec boutons Play, Pause, Stop
        player_frame = tk.Frame(self.root)
        player_frame.pack(pady=10)
        
        button_play_original = tk.Button(player_frame, text="Lire avant nettoyage", command=self.play_original_audio)
        button_play_original.grid(row=0, column=0, padx=5)

        button_play_cleaned = tk.Button(player_frame, text="Lire après nettoyage", command=self.play_cleaned_audio)
        button_play_cleaned.grid(row=0, column=1, padx=5)

        button_stop = tk.Button(player_frame, text="Stop", command=self.stop_audio)
        button_stop.grid(row=0, column=4, padx=5)

        # Graphique pour comparer les spectres audio avant/après
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=(12, 6))
        self.fig.tight_layout(pad=5.0)
        self.canvas = None

        # Bouton pour enregistrer le fichier nettoyé
        button_save = tk.Button(self.root, text="Enregistrer le fichier nettoyé", command=self.on_save_click)
        button_save.pack(pady=10)

        self.file_path = None  # Pour stocker le chemin du fichier sélectionné
        self.cleaned_audio = None  # Pour stocker le chemin du fichier nettoyé

        ttk.Separator(orient='horizontal')
        self.progressbar = ttk.Progressbar(self.root, length=773, orien='horizontal', mod='determinate')
        self.progressbar.pack(padx = (13, 0))

    def stop_audio(self):
        pygame.mixer.music.stop()
        self.playing = False

    def on_select_file(self):
        self.file_path = filedialog.askopenfilename(
            filetypes=[("Fichiers audio/vidéo", "*.mp3 *.wav *.flac *.ogg *.mp4 *.mkv *.avi *.mov")]
        )

        if self.file_path:
          self.label_file.config(text=self.file_path)
          self.display_file_info(self.file_path)

          # Détecter si c'est une vidéo
          if any(self.file_path.endswith(ext) for ext in ['.mp4', '.mkv', '.avi', '.mov']):
            self.video_path = self.file_path
          else:
            self.video_path = None

        self.stop_audio()

        self.wav_file = convert_to_wav(self.file_path, temp_dir=self.temp_dir)

    def display_file_info(self, file_path):
        try:
            channels, sample_width, frame_rate, self.duration = get_audio_metadata(file_path)
            audio_info = f"Canaux: {channels}, Echantillonnage: {frame_rate}Hz, Durée: {self.duration:.2f} secondes"
            self.label_info.config(text=audio_info)
        except Exception as e:
            self.label_info.config(text=f"Erreur lors de la lecture du fichier : {str(e)}")

    def on_clean_click(self):
        if not self.file_path:
            messagebox.showerror("Erreur", "Veuillez sélectionner un fichier avant de nettoyer.")
            return

        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        options = {
            'postfilter': self.postfilter_var.get(),
            'pf_beta': self.pf_beta_var.get(),
            'atten_lim_db': self.atten_lim_db_var.get(),
        }

        try:
            # Afficher le message d'attente
            self.spinner_label.config(text="Traitement en cours...")
            threading.Thread(target=self.process_file, args=(self.output_dir, options)).start()
        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    def plot_spectrogram(self, original_file, cleaned_file):
        original_audio, sr = librosa.load(original_file, sr=None)
        cleaned_audio, sr = librosa.load(cleaned_file, sr=None)

        # Spectrogramme original
        self.ax1.clear()
        D_original = librosa.amplitude_to_db(librosa.stft(original_audio), ref=np.max)
        librosa.display.specshow(D_original, sr=sr, x_axis='time', y_axis='log', ax=self.ax1)
        #self.ax1.ylabel("avant")

        # Spectrogramme nettoyé
        self.ax2.clear()
        D_cleaned = librosa.amplitude_to_db(librosa.stft(cleaned_audio), ref=np.max)
        librosa.display.specshow(D_cleaned, sr=sr, x_axis='time', y_axis='log', ax=self.ax2)
        #self.ax2.ylabel("après")

        # Redessiner le canvas avec les nouveaux spectrogrammes
        self.canvas.draw()

    def process_file(self, output_dir, options):
        # Convertir en WAV si nécessaire avant de traiter avec DeepFilterNet
        process_audio(self.wav_file, output_dir, options)
        # Planifie l'exécution de la fonction on_process_complete dans le thread principal
        self.root.after(0, self.on_process_complete, output_dir)

    def on_process_complete(self, output_dir):
        # Mise à jour de l'interface après le traitement
        
        # modifie le nom du fichier créé pour éviter les locks de fichiers en lecture
        uid = uuid.uuid4().hex + '.wav'
        os.rename(os.path.join(output_dir, os.path.basename(self.wav_file)), os.path.join(output_dir, uid))

        # Stocker le fichier nettoyé
        self.cleaned_audio = os.path.join(output_dir, os.path.join(output_dir, uid))

        # Visualiser les courbes audio avant/après
        self.plot_spectrogram(self.wav_file, self.cleaned_audio)

        # Mise à jour du label et alerte
        self.spinner_label.config(text="")
        messagebox.showinfo("Terminé", "Le nettoyage est terminé!")

    def update_playback_progress(self):
        # Mise à jour de la barre de progression pendant la lecture
        while self.playing :
            current_pos = ((time.time() - self.start_time) / self.duration)*100
            self.progressbar.config(value=current_pos)
            
            time.sleep(0.1)  # Rafraîchissement toutes les 100 ms

    def play_original_audio(self):
        if self.file_path:
            pygame.mixer.music.load(self.wav_file)
            pygame.mixer.music.play()
            self.playing = True
            self.start_time = time.time()
            threading.Thread(target=self.update_playback_progress, daemon=True).start()

    def play_cleaned_audio(self):
        if self.cleaned_audio:
            pygame.mixer.music.load(self.cleaned_audio)
            pygame.mixer.music.play()
            self.playing = True
            self.start_time = time.time()
            threading.Thread(target=self.update_playback_progress, daemon=True).start()

    def on_save_click(self):
        if self.cleaned_audio:
            if self.video_path == None : 
                filetypes = [("Fichiers audio", "*.wav *.mp3 *.flac")]
                save_path = filedialog.asksaveasfilename(defaultextension=".wav", filetypes=filetypes)
                if save_path:
                    # Convertir et enregistrer dans le format sélectionné
                    converted_file = convert_to_wav(self.cleaned_audio, output_format=save_path.split('.')[-1])
                    os.rename(converted_file, save_path)
                    messagebox.showinfo("Sauvegardé", f"Fichier sauvegardé à {save_path}")
            else :  #si c'est une vidéo
                filetypes = [("Fichiers vidéo", "*.mp4"), ("Fichiers audio", "*.wav *.mp3 *.flac")]
                save_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=filetypes)
                output_format = save_path.split('.')[-1].lower() 
                if save_path:
                    if output_format in ['mp4', 'mkv']:
                        # modifier le nom et enregistrer dans le format sélectionné
                        self.spinner_label.config(text="Reconstruction et enregistrement de la vidéo en cours...")
                        reconstruct_video_from_audio_and_video(self.video_path, self.cleaned_audio, save_path)
                        self.spinner_label.config(text="")
                        #os.rename(os.path.join(self.output_dir, os.path.basename(self.video_path)), save_path)
                    else :
                        converted_file = convert_to_wav(self.cleaned_audio, output_format=save_path.split('.')[-1])
                        os.rename(converted_file, save_path)
                    messagebox.showinfo("Sauvegardé", f"Fichier sauvegardé à {save_path}")

    def on_close(self):
        # Code pour arrêter proprement le programme
        # Arrêter les traitements en cours (voir ci-dessous)
        #self.stop_processes() 
        try:
            # Supprimer les dossiers temp
            self.temp_dir_obj.cleanup() 
            self.output_dir_obj.cleanup()
        except OSError as e:
            print(f"Erreur lors du nettoyage des dossiers : {e}")
        # Nettoyer les dossiers temp et output
        self.root.destroy()  
        quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioCleanerApp(root)
    root.mainloop()