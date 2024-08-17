# Nettoyage Audio/Video avec DeepFilterNet

![App Icon](./assets/icon.jpg)  DeepFilterNetGui

## Description

Cette application Python avec une interface graphique en Tkinter permet de nettoyer les bruits parasites dans des fichiers audio ou vidéo en utilisant l'outil [**DeepFilterNet**](https://github.com/Rikorose/DeepFilterNet). 
Elle a pour but de simplifier l'utilisation de DeepFilterNet avec une interface graphique et des conversions automatiques des formats audio/vidéo. 
Les traitements sont rapides et se font localement.

## Usage
1. Lancer l'application :

    ```bash
    python main.py
    ```
    
- **Choisir un fichier audio/vidéo** : Importation facile de fichiers audio et vidéo.
- **Visualiser des métadonnées** : Informations sur le fichier audio/vidéo importé (format, échantillonnage, durée, etc.).
- **Ajuster les options de traitement** : Paramètres ajustables pour le post-filtrage et l'atténuation.
- **Lancer le nettoyage des fichiers audio** : Utilisation de DeepFilterNet pour nettoyer les bruits parasites.
- **tester grace au lecteur audio** : Lecture avant/après nettoyage, avec la possibilité de visualiser les spectrogrammes.
- **Exporter** : Sauvegarde du fichier nettoyé dans différents formats audio/vidéo.

## Capture d'écran

![Capture d'écran de l'application](./assets/screenshot..png)

## Prérequis

- **Python 3.8+**
- **DeepFilterNet** (sous forme d'exécutable)
- **FFmpeg** (pour la gestion des formats vidéo)
- **Pygame** (pour la gestion du lecteur audio)
- **MoviePy** (pour la gestion des vidéos)
- **Pydub** (pour la manipulation des fichiers audio)
- **librosa** (pour la manipulation des fichiers audio)
- **Matplotlib** (pour la visualisation des spectrogrammes)

## Installation

1. Clonez le dépôt :

    ```bash
    git clone https://github.com/dbwa/DeepFilterNetGui.git
    cd NettoyageAudioVideo
    ```

2. Créez et activez un environnement virtuel Python :

    ```bash
    python -m venv env
    source env/bin/activate  # Sur Windows: env\Scripts\activate
    ```

3. Installez les dépendances :

    ```bash
    pip install -r requirements.txt
    ```

4. Installez FFmpeg :

    Suivez les instructions officielles pour installer FFmpeg : https://ffmpeg.org/download.html
    
    
5. Installer DeepFilterNet

    - Télécharger l'exécutable depuis https://github.com/Rikorose/DeepFilterNet/releases/ et le renommer en **deep-filter.exe** (wondows) ou **deep-filter** (linux)
    - Assurez-vous que l'exécutable deep-filter est disponible dans votre `PATH` ou dans le répertoire du projet.


## Structure du projet

```bash
deepfilter_gui/
│
├── main.py                      # Le fichier principal de l'application
├── deepfilter_interface.py      # Interface avec DeepFilterNet
├── utils.py                     # Fonctions utilitaires pour conversion, visualisation, etc.
├── requirements.txt             # Librairies pythons à installer.
└── assets/
    ├── icon.png                 # Icône de l'application
    └── screenshot.png           # Capture d'écran de l'application
```

## Contribuer
Les contributions sont les bienvenues ! Pour contribuer :
1. Fork le projet
2. Créez une nouvelle branche (git checkout -b feature/NouvelleFonctionnalité)
3. Commitez vos changements (git commit -am 'Ajout d'une nouvelle fonctionnalité')
4. Poussez vos changements (git push origin feature/NouvelleFonctionnalité)
5. Ouvrez une Pull Request

## Licence
Ce projet est sous licence MIT. Consultez le fichier LICENSE pour plus d'informations.

## Crédits
DeepFilterNet : https://github.com/Rikorose/DeepFilterNet


17/08/2024
