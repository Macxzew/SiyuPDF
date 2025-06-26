import shutil
import time
import sys
import os

from siyupdf.config import TMP_PDF_PATH1, TMP_PDF_PATH2, RESOURCES_PATH, TMP_WATERMARK_PATH
from tkinter import Tk, filedialog
from colorama import Fore, Style


def prepare_env():
    """
    Gère l'importation d'un fichier PDF, effectue la copie vers TMP_PDF_PATH1,
    et prépare les répertoires nécessaires.
    """
    print(f"\n{Fore.MAGENTA}Importation du fichier PDF... {Style.RESET_ALL}")
    ORIGINAL_PDF_PATH = None
    try:
        root = Tk()
        root.withdraw()
        ORIGINAL_PDF_PATH = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        root.destroy()
    except ImportError:
        print(f"{Fore.YELLOW}Tkinter non disponible. Veuillez entrer le chemin du fichier PDF :")
    except Exception as e:
        print(f"{Fore.RED}Erreur Tkinter : {e}. Passez en CLI pour continuer.")
    if not ORIGINAL_PDF_PATH:
        print(f"{Fore.YELLOW}Veuillez entrer le chemin du fichier PDF :")
        user_input = input(f"{Fore.MAGENTA}> {Style.RESET_ALL}").strip()
        if os.path.isfile(user_input) and user_input.lower().endswith(".pdf"):
            ORIGINAL_PDF_PATH = user_input
    if not ORIGINAL_PDF_PATH:
        print(f"{Fore.RED}Aucun fichier PDF valide fourni. Fermeture de l'application.{Style.RESET_ALL}")
        sys.exit(1)
    # Extraire le nom du fichier d'origine
    ORIGINAL_PDF_NAME = os.path.basename(ORIGINAL_PDF_PATH)
    print(f"{Fore.CYAN}Traitement du fichier : {ORIGINAL_PDF_NAME}")
    # Préparer le répertoire de ressources
    os.makedirs(RESOURCES_PATH, exist_ok=True)
    # Copier le fichier original vers TMP_PDF_PATH1
    shutil.copy(ORIGINAL_PDF_PATH, TMP_PDF_PATH1)
    return ORIGINAL_PDF_NAME


def animated_status(message, cycles=2, delay=0.01):
    """
    Affiche un message avec un effet de "spinner" animé à la fin du message,
    puis indique la fin du traitement avec "Traitement terminé √".
    """
    spinner = ['.', '..', '...', ' ..', '  .', ' ..', '...', '.. ', '.  ', '']
    spinner_length = len(spinner)
    print(f"{Fore.YELLOW}{message}", end='', flush=True)
    total_iterations = cycles * spinner_length
    for i in range(total_iterations):
        spin_index = i % spinner_length
        sys.stdout.write('\r' + Fore.YELLOW + message + spinner[spin_index])
        sys.stdout.flush()
        time.sleep(delay)
    # Effacer la ligne après la fin de l'animation pour éviter les chevauchements
    print('\r' + ' ' * (len(message) + len(spinner[-1]) + 20), end='')  # Assure un nettoyage complet de la ligne
    # Afficher le message final avec le symbole de coche
    print(f"\r{Fore.GREEN}Traitement terminé √")


def clean_tmp():
    """
    Supprime les fichiers temporaires TMP_PDF_PATH et TMP_WATERMARK_PATH.
    """
    for temp_file in [TMP_PDF_PATH1, TMP_PDF_PATH2, TMP_WATERMARK_PATH]:
        if os.path.exists(temp_file):
            os.remove(temp_file)
