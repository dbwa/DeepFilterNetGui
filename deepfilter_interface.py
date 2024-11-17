import subprocess

def process_audio(input_wav, output_dir, options={}):
    """
    Appelle DeepFilterNet pour traiter un fichier audio avec les options spécifiées.
    """
    print("[DEBUG] Début de process_audio")
    print(f"[DEBUG] Paramètres reçus: input={input_wav}, output_dir={output_dir}, options={options}")
    
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
    
    print(f"[DEBUG] Commande complète: {' '.join(command)}")
    
    try:
        # Exécuter la commande et capturer la sortie
        result = subprocess.run(command, capture_output=True, text=True)
        print(f"[DEBUG] Sortie standard: {result.stdout}")
        print(f"[DEBUG] Sortie d'erreur: {result.stderr}")
        print(f"[DEBUG] Code de retour: {result.returncode}")
        
        if result.returncode != 0:
            print(f"[ERROR] La commande a échoué avec le code {result.returncode}")
            
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'exécution de la commande: {str(e)}")
        raise
    
    print("[DEBUG] Fin de process_audio")