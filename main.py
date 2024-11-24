import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QPushButton, 
                            QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, 
                            QProgressBar, QSlider, QStyle, QMessageBox, 
                            QStatusBar)
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from deepfilter_interface import process_audio
from utils import convert_to_wav, convert_audio_format, reconstruct_video_from_audio_and_video
import tempfile
import uuid
import numpy as np
import librosa
import librosa.display
import time

# Ajout d'une classe pour gérer le traitement en arrière-plan
class AudioProcessingThread(QThread):
    finished = pyqtSignal(str)  # Signal émis quand le traitement est terminé
    progress = pyqtSignal(int)  # Signal pour mettre à jour la progression
    error = pyqtSignal(str)     # Signal en cas d'erreur

    def __init__(self, input_file, output_dir):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir

    def run(self):
        try:
            # Récupérer le nom du fichier d'entrée
            input_basename = os.path.basename(self.input_file)
            # Le fichier de sortie aura initialement le même nom
            temp_output = os.path.join(self.output_dir, input_basename)
            # Le nom final avec un UUID
            final_output = os.path.join(self.output_dir, f"{uuid.uuid4().hex}.wav")
            
            print(f"[DEBUG] Fichier d'entrée: {self.input_file}")
            print(f"[DEBUG] Fichier de sortie temporaire attendu: {temp_output}")
            print(f"[DEBUG] Fichier de sortie final: {final_output}")
            
            # Options par défaut pour DeepFilterNet
            options = {
                'postfilter': True,
                'pf_beta': 0.02,
                'atten_lim_db': 100
            }
            
            # Traitement audio
            self.progress.emit(10)
            process_audio(self.input_file, self.output_dir, options)
            self.progress.emit(90)
            
            # Vérifier si le fichier de sortie existe et le renommer
            if os.path.exists(temp_output):
                print(f"[DEBUG] Renommage du fichier: {temp_output} -> {final_output}")
                os.rename(temp_output, final_output)
                self.progress.emit(100)
                self.finished.emit(final_output)
            else:
                raise Exception(f"Le fichier de sortie n'a pas été créé. Contenu du dossier: {os.listdir(self.output_dir)}")
            
        except Exception as e:
            print(f"[ERROR] Une erreur est survenue: {str(e)}")
            self.error.emit(str(e))

class AudioPlayer(QWidget):
    def __init__(self, title="Lecteur Audio"):
        super().__init__()
        self.title = title
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Titre
        title_label = QLabel(self.title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Contrôles de lecture
        controls_layout = QHBoxLayout()
        
        # Boutons avec icônes du système
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        
        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.stop_button)
        layout.addLayout(controls_layout)
        
        # Slider de position
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        layout.addWidget(self.position_slider)
        
        # Labels de temps
        time_layout = QHBoxLayout()
        self.time_label = QLabel("0:00 / 0:00")
        time_layout.addWidget(self.time_label)
        layout.addLayout(time_layout)
        
        # Volume
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(70)
        volume_layout.addWidget(self.volume_slider)
        layout.addLayout(volume_layout)
        
        self.setLayout(layout)
        
    def setup_connections(self):
        self.play_button.clicked.connect(self.toggle_play)
        self.stop_button.clicked.connect(self.stop)
        self.position_slider.sliderMoved.connect(self.set_position)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.media_player.positionChanged.connect(self.position_changed)
        self.media_player.durationChanged.connect(self.duration_changed)
        
    def set_audio_file(self, file_path):
        self.media_player.setSource(QUrl.fromLocalFile(file_path))
        self.audio_output.setVolume(self.volume_slider.value() / 100)
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        
    def toggle_play(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        else:
            self.media_player.play()
            self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPause))
            
    def stop(self):
        self.media_player.stop()
        self.play_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        
    def set_position(self, position):
        self.media_player.setPosition(position)
        
    def set_volume(self, volume):
        self.audio_output.setVolume(volume / 100)
        
    def position_changed(self, position):
        self.position_slider.setValue(position)
        self.update_time_label()
        
    def duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self.update_time_label()
        
    def update_time_label(self):
        position = self.media_player.position()
        duration = self.media_player.duration()
        self.time_label.setText(f"{self.format_time(position)} / {self.format_time(duration)}")
        
    @staticmethod
    def format_time(ms):
        s = round(ms / 1000)
        m, s = divmod(s, 60)
        return f"{m}:{s:02d}"

class AudioCleanerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DeepFilterNet GUI")
        self.setMinimumSize(800, 600)
        
        # Widget principal
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Bouton de sélection de fichier
        self.select_button = QPushButton("Sélectionner un fichier")
        self.select_button.clicked.connect(self.on_select_file)
        layout.addWidget(self.select_button)
        
        # Label pour le fichier sélectionné
        self.file_label = QLabel("Aucun fichier sélectionné")
        layout.addWidget(self.file_label)
        
        # Spectrogrammes avec un style amélioré
        plt.style.use('dark_background')
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(8, 4))
        self.fig.patch.set_alpha(0.0)  # Fond transparent
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setStyleSheet("background-color: transparent;")  # Rend le widget transparent
        layout.addWidget(self.canvas)
        
        # Image de démarrage
        self.setup_initial_plot()
        
        # Lecteurs audio
        players_layout = QHBoxLayout()
        self.original_player = AudioPlayer("Audio Original")
        self.cleaned_player = AudioPlayer("Audio Nettoyé")
        players_layout.addWidget(self.original_player)
        players_layout.addWidget(self.cleaned_player)
        layout.addLayout(players_layout)
        
        # Bouton de nettoyage
        self.clean_button = QPushButton("Nettoyer l'audio")
        self.clean_button.clicked.connect(self.on_clean_click)
        layout.addWidget(self.clean_button)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)
        
        # Bouton de sauvegarde
        self.save_button = QPushButton("Sauvegarder")
        self.save_button.clicked.connect(self.on_save_click)
        layout.addWidget(self.save_button)
        
        # Ajout d'une barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Initialisation du thread de traitement
        self.processing_thread = None
        
        # Désactiver certains boutons au démarrage
        self.clean_button.setEnabled(False)
        self.save_button.setEnabled(False)
        
        # Création des dossiers temporaires
        self.temp_dir_obj = tempfile.TemporaryDirectory(prefix='deepfilterapp_temp_')
        self.temp_dir = self.temp_dir_obj.name
        self.output_dir_obj = tempfile.TemporaryDirectory(prefix='deepfilterapp_output_')
        self.output_dir = self.output_dir_obj.name

    def setup_initial_plot(self):
        """Configure l'affichage initial avec une animation de type oscilloscope"""
        self.ax1.clear()
        self.ax2.clear()
        
        # Désactiver les axes et grilles
        for ax in [self.ax1, self.ax2]:
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_frame_on(False)
            ax.set_facecolor('none')  # Fond transparent
        
        # Créer une onde sinusoïdale stylisée
        x = np.linspace(0, 4*np.pi, 1000)
        y = 0.3 * np.sin(x) * np.exp(-x/10)
        
        # Tracer l'onde dans le premier axe
        self.ax1.plot(x, y, color='#4a9eff', alpha=0.5, linewidth=2)
        self.ax1.plot(x, -y, color='#4a9eff', alpha=0.5, linewidth=2)
        self.ax1.text(0, 1, 'En attente du fichier audio', 
                      ha='center', va='center', color='#4a9eff',
                      fontsize=12, alpha=0.8,
                      bbox=dict(facecolor='none', edgecolor='none'))
        
        # Tracer une forme d'onde différente dans le second axe
        y2 = 0.3 * np.sin(2*x) * np.exp(-x/8)
        self.ax2.plot(x, y2, color='#4a9eff', alpha=0.5, linewidth=2)
        self.ax2.plot(x, -y2, color='#4a9eff', alpha=0.5, linewidth=2)

        
        # Ajuster les limites pour centrer l'onde
        for ax in [self.ax1, self.ax2]:
            ax.set_ylim(-1, 1)
        
        self.fig.patch.set_alpha(0.0)  # S'assurer que le fond est transparent
        self.fig.tight_layout()
        self.canvas.draw()

    def on_select_file(self):
        self.file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier audio/vidéo",
            "",
            "Fichiers audio/vidéo (*.mp3 *.wav *.flac *.ogg *.m4a *.mp4 *.mkv *.avi *.mov)"  # Ajout de *.m4a
        )
        
        if self.file_path:
            print(f"\n[DEBUG] Fichier sélectionné: {self.file_path}")
            print(f"[DEBUG] Extension: {os.path.splitext(self.file_path)[1]}")
            
            # Vérifier d'abord si c'est un fichier audio
            audio_extensions = {'.mp3', '.wav', '.flac', '.ogg', '.m4a'}  # Ajout de .m4a
            if os.path.splitext(self.file_path)[1].lower() in audio_extensions:
                print("[DEBUG] Fichier audio détecté")
                self.video_path = None
                self.is_video = False
            else:
                # Si ce n'est pas un fichier audio, essayer de l'ouvrir comme vidéo
                try:
                    from moviepy.editor import VideoFileClip
                    print("[DEBUG] Tentative d'ouverture comme vidéo...")
                    video = VideoFileClip(self.file_path)
                    
                    print(f"[DEBUG] Attributs de la vidéo:")
                    print(f"[DEBUG] - Durée: {video.duration}")
                    print(f"[DEBUG] - Taille: {video.size}")
                    print(f"[DEBUG] - FPS: {video.fps}")
                    print(f"[DEBUG] - Audio présent: {video.audio is not None}")
                    print(f"[DEBUG] - Rotation: {video.rotation}")
                    
                    if video.size is not None and video.fps is not None:
                        print("[DEBUG] ✓ C'est une vidéo (détecté via size et fps)")
                        self.status_bar.showMessage("Fichier vidéo détecté, extraction de l'audio...")
                        self.video_path = self.file_path
                        self.is_video = True
                    else:
                        print("[DEBUG] ✗ Pas de piste vidéo trouvée")
                        self.video_path = None
                        self.is_video = False
                    video.close()
                    
                except Exception as e:
                    print(f"[DEBUG] ✗ Erreur lors de la vérification vidéo: {str(e)}")
                    self.video_path = None
                    self.is_video = False

            try:
                # Conversion en WAV pour le traitement
                print("[DEBUG] Conversion en WAV...")
                self.wav_file = convert_to_wav(self.file_path, self.temp_dir)
                print(f"[DEBUG] Fichier WAV créé: {self.wav_file}")
                
                # Mise à jour de l'interface
                self.file_label.setText(os.path.basename(self.file_path))
                self.clean_button.setEnabled(True)
                self.status_bar.showMessage("Fichier prêt pour le traitement")
                
            except Exception as e:
                print(f"[DEBUG] Erreur lors de la conversion WAV: {str(e)}")
                self.status_bar.showMessage("Erreur lors de la préparation du fichier")
                QMessageBox.critical(self, "Erreur", f"Impossible de préparer le fichier:\n{str(e)}")
                return
            
            print(f"[DEBUG] État final - is_video: {hasattr(self, 'is_video')} = {getattr(self, 'is_video', None)}")
            print(f"[DEBUG] État final - video_path: {hasattr(self, 'video_path')} = {getattr(self, 'video_path', None)}")

    def on_clean_click(self):
        if not hasattr(self, 'wav_file'):
            QMessageBox.warning(self, "Erreur", "Veuillez d'abord sélectionner un fichier.")
            return

        # Désactiver les boutons pendant le traitement
        self.clean_button.setEnabled(False)
        self.select_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.progress_bar.setValue(0)
        
        # Créer et démarrer le thread de traitement
        self.processing_thread = AudioProcessingThread(self.wav_file, self.output_dir)
        self.processing_thread.progress.connect(self.update_progress)
        self.processing_thread.finished.connect(self.on_processing_finished)
        self.processing_thread.error.connect(self.on_processing_error)
        
        self.status_bar.showMessage("Traitement en cours...")
        self.processing_thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def on_processing_finished(self, output_file):
        # Réactiver les boutons
        self.clean_button.setEnabled(True)
        self.select_button.setEnabled(True)
        self.save_button.setEnabled(True)
        
        # Mettre à jour l'interface
        self.progress_bar.setValue(80)  # 80% avant les spectrogrammes
        self.status_bar.showMessage("Génération des spectrogrammes...")
        
        # Stocker le chemin du fichier nettoyé
        self.cleaned_audio = output_file
        print(f"[DEBUG] Fichier nettoyé stocké: {self.cleaned_audio}")
        
        # Mettre à jour les lecteurs audio et spectrogrammes
        self.original_player.set_audio_file(self.wav_file)
        self.cleaned_player.set_audio_file(self.cleaned_audio)
        self.plot_spectrograms(self.wav_file, self.cleaned_audio)
        
        # Finaliser
        self.progress_bar.setValue(100)
        self.status_bar.showMessage("Traitement terminé avec succès!", 5000)
        
        # Afficher une notification
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("Le traitement est terminé!")
        msg.setWindowTitle("Succès")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

    def on_processing_error(self, error_message):
        # Réactiver les boutons
        self.clean_button.setEnabled(True)
        self.select_button.setEnabled(True)
        
        # Afficher l'erreur
        self.status_bar.showMessage("Erreur lors du traitement!", 5000)
        QMessageBox.critical(self, "Erreur", f"Une erreur est survenue:\n{error_message}")

    def on_save_click(self):
        if not hasattr(self, 'cleaned_audio'):
            QMessageBox.warning(self, "Erreur", "Aucun fichier traité à sauvegarder.")
            return

        print(f"[DEBUG] cleaned_audio: {self.cleaned_audio}")
        print(f"[DEBUG] Attributs vidéo - is_video: {hasattr(self, 'is_video')} = {getattr(self, 'is_video', None)}")
        print(f"[DEBUG] Attributs vidéo - video_path: {hasattr(self, 'video_path')} = {getattr(self, 'video_path', None)}")

        # Déterminer le format d'origine
        original_ext = os.path.splitext(self.file_path)[1].lower()
        print(f"[DEBUG] Format d'origine: {original_ext}")
        
        # Si c'est une vidéo, demander à l'utilisateur
        if hasattr(self, 'is_video') and self.is_video:
            print("[DEBUG] Demande à l'utilisateur (vidéo détectée)")
            choice = QMessageBox.question(
                self,
                "Type de sauvegarde",
                "Voulez-vous sauvegarder la vidéo avec l'audio nettoyé ou seulement l'audio nettoyé?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            save_as_video = (choice == QMessageBox.StandardButton.Yes)
            print(f"[DEBUG] Choix utilisateur - save_as_video: {save_as_video}")
        else:
            print("[DEBUG] Pas de vidéo détectée, sauvegarde en audio")
            save_as_video = False

        # Préparer les filtres pour le dialogue de sauvegarde
        if save_as_video:
            filters = (
                "Format d'origine (*" + original_ext + ");;"
                "Vidéo MP4 (*.mp4);;"
                "Vidéo MKV (*.mkv);;"
                "Vidéo AVI (*.avi);;"
                "Vidéo MOV (*.mov)"
            )
        else:
            filters = (
                "Format d'origine (*" + original_ext + ");;"
                "Audio WAV (*.wav);;"
                "Audio MP3 (*.mp3);;"
                "Audio FLAC (*.flac);;"
                "Audio OGG (*.ogg);;"
                "Audio M4A (*.m4a)"
            )

        # Ouvrir le dialogue de sauvegarde
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Sauvegarder le fichier",
            "",
            filters
        )
        
        if file_path:
            try:
                print(f"[DEBUG] Sauvegarde vers: {file_path}")
                self.status_bar.showMessage("Sauvegarde en cours...")
                desired_ext = os.path.splitext(file_path)[1].lower()
                print(f"[DEBUG] Extension désirée: {desired_ext}")
                
                if save_as_video and self.is_video:
                    print("[DEBUG] Début reconstruction vidéo")
                    self.status_bar.showMessage("Reconstruction de la vidéo en cours... Cette opération peut prendre plusieurs minutes.")
                    reconstruct_video_from_audio_and_video(
                        self.video_path,
                        self.cleaned_audio,
                        file_path,
                        format=desired_ext[1:]
                    )
                    print("[DEBUG] Fin reconstruction vidéo")
                else:
                    print("[DEBUG] Début conversion audio")
                    convert_audio_format(
                        self.cleaned_audio,
                        file_path,
                        format=desired_ext[1:]
                    )
                    print("[DEBUG] Fin conversion audio")
                
                self.status_bar.showMessage("Sauvegarde terminée avec succès!", 5000)
                QMessageBox.information(
                    self,
                    "Succès",
                    "Le fichier a été sauvegardé avec succès!"
                )
                
            except Exception as e:
                print(f"[ERROR] Erreur lors de la sauvegarde: {str(e)}")
                self.status_bar.showMessage("Erreur lors de la sauvegarde!", 5000)
                QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la sauvegarde:\n{str(e)}")

    def plot_spectrograms(self, original_file, cleaned_file):
        """Affiche les spectrogrammes des fichiers audio"""
        # Paramètres configurables pour l'optimisation
        SAMPLE_RATE = int(22050/4)        # Fréquence d'échantillonnage (22050 Hz = environ 1/2 de 44100 Hz)
        N_FFT = int(2048/2)              # Taille de la FFT (défaut=2048). Plus grand = moins de résolution temporelle
        HOP_LENGTH = int(512*4)          # Nombre d'échantillons entre trames successives (défaut=512)
                                 # Plus grand = moins de colonnes temporelles
        
        start_time = time.time()
        try:
            print("[DEBUG] Génération des spectrogrammes...")
            print(f"[DEBUG] Paramètres: sr={SAMPLE_RATE}Hz, n_fft={N_FFT}, hop_length={HOP_LENGTH}")
            
            # Nettoyer les axes
            self.ax1.clear()
            self.ax2.clear()
            
            # Configuration des axes pour la transparence
            for ax in [self.ax1, self.ax2]:
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_frame_on(False)
                ax.set_facecolor('none')
            
            # Charger les fichiers audio avec fréquence réduite
            y_orig, sr = librosa.load(original_file, sr=SAMPLE_RATE)
            y_clean, _ = librosa.load(cleaned_file, sr=SAMPLE_RATE)
            
            print(f"[DEBUG] Chargement audio: {time.time() - start_time:.2f}s")
            
            # Calculer les spectrogrammes avec résolution réduite
            D_orig = librosa.amplitude_to_db(
                abs(librosa.stft(y_orig, n_fft=N_FFT, hop_length=HOP_LENGTH)), 
                ref=np.max
            )
            D_clean = librosa.amplitude_to_db(
                abs(librosa.stft(y_clean, n_fft=N_FFT, hop_length=HOP_LENGTH)), 
                ref=np.max
            )
            
            print(f"[DEBUG] Calcul spectrogrammes: {time.time() - start_time:.2f}s")
            
            # Afficher les spectrogrammes avec un style amélioré
            img1 = librosa.display.specshow(D_orig, ax=self.ax1, cmap='magma',
                                          hop_length=HOP_LENGTH, sr=SAMPLE_RATE)
            img2 = librosa.display.specshow(D_clean, ax=self.ax2, cmap='magma',
                                          hop_length=HOP_LENGTH, sr=SAMPLE_RATE)
            
            # Titres stylisés
            self.ax1.text(0.02, 0.95, 'Signal Original', 
                         transform=self.ax1.transAxes,
                         color='white', fontsize=10, alpha=0.8)
            self.ax2.text(0.02, 0.95, 'Signal Nettoyé', 
                         transform=self.ax2.transAxes,
                         color='white', fontsize=10, alpha=0.8)
            
            # Ajuster la mise en page
            self.fig.tight_layout()
            self.canvas.draw()
            
            # S'assurer que le fond reste transparent
            self.fig.patch.set_alpha(0.0)
            self.canvas.draw()
            
            print(f"[DEBUG] Spectrogrammes générés avec succès en {time.time() - start_time:.2f} secondes")
            
        except Exception as e:
            print(f"[ERROR] Erreur lors de la génération des spectrogrammes: {str(e)}")
            self.status_bar.showMessage("Erreur lors de la génération des spectrogrammes", 5000)

    def closeEvent(self, event):
        print("[DEBUG] Début de la fermeture de l'application")
        try:
            # 1. Arrêter et libérer les lecteurs audio
            if hasattr(self, 'original_player'):
                print("[DEBUG] Arrêt du lecteur original")
                self.original_player.media_player.stop()
                self.original_player.media_player.setSource(QUrl())  # Libérer la source
                self.original_player.media_player.deleteLater()
                
            if hasattr(self, 'cleaned_player'):
                print("[DEBUG] Arrêt du lecteur nettoyé")
                self.cleaned_player.media_player.stop()
                self.cleaned_player.media_player.setSource(QUrl())  # Libérer la source
                self.cleaned_player.media_player.deleteLater()
            
            # 2. Attendre un peu que les ressources soient libérées
            QApplication.processEvents()
            time.sleep(0.5)  # Petit délai pour laisser le temps aux ressources d'être libérées
            
            # 3. Nettoyer les dossiers temporaires
            if hasattr(self, 'temp_dir_obj'):
                try:
                    print(f"[DEBUG] Nettoyage du dossier temporaire: {self.temp_dir}")
                    # Supprimer les fichiers manuellement d'abord
                    for filename in os.listdir(self.temp_dir):
                        filepath = os.path.join(self.temp_dir, filename)
                        if os.path.isfile(filepath):
                            try:
                                os.chmod(filepath, 0o777)  # Donner tous les droits
                                os.unlink(filepath)
                                print(f"[DEBUG] Fichier supprimé: {filepath}")
                            except Exception as e:
                                print(f"[DEBUG] Impossible de supprimer {filepath}: {str(e)}")
                    
                    # Puis laisser cleanup faire son travail
                    self.temp_dir_obj.cleanup()
                    print("[DEBUG] Nettoyage temp_dir réussi")
                except Exception as e:
                    print(f"[DEBUG] Erreur nettoyage temp_dir: {str(e)}")
            
            if hasattr(self, 'output_dir_obj'):
                try:
                    print(f"[DEBUG] Nettoyage du dossier de sortie: {self.output_dir}")
                    # Supprimer les fichiers manuellement d'abord
                    for filename in os.listdir(self.output_dir):
                        filepath = os.path.join(self.output_dir, filename)
                        if os.path.isfile(filepath):
                            try:
                                os.chmod(filepath, 0o777)  # Donner tous les droits
                                os.unlink(filepath)
                                print(f"[DEBUG] Fichier supprimé: {filepath}")
                            except Exception as e:
                                print(f"[DEBUG] Impossible de supprimer {filepath}: {str(e)}")
                    
                    # Puis laisser cleanup faire son travail
                    self.output_dir_obj.cleanup()
                    print("[DEBUG] Nettoyage output_dir réussi")
                except Exception as e:
                    print(f"[DEBUG] Erreur nettoyage output_dir: {str(e)}")
                    
        except Exception as e:
            print(f"[DEBUG] Erreur lors de la fermeture: {str(e)}")
        
        print("[DEBUG] Fin de la fermeture de l'application")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AudioCleanerApp()
    window.show()
    sys.exit(app.exec())