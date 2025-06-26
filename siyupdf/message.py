import shutil
import os
import re

from siyupdf.config import RESULTS_PATH, TMP_PDF_PATH1
from tkinter import filedialog, Tk
from colorama import Fore, Style, init

init(autoreset=True)

def strip_ansi(line):
    # Retire toutes les séquences ANSI (couleurs)
    return re.sub(r'\x1b\[[0-9;]*m', '', line)

def welcome():
    """
    Affiche un message de bienvenue avec un cadre dynamique,
    titres en magenta, reste sobre.
    """
    os.system("cls" if os.name == "nt" else "clear")
    lines = [
        f"{Fore.MAGENTA}Bienvenue dans l'outil SiyuPDF !{Style.RESET_ALL}",
        f"{Fore.LIGHTMAGENTA_EX}macxzew{Style.RESET_ALL} | {Fore.MAGENTA}1.0{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}{'-' * 34}{Style.RESET_ALL}",
        "",
        f"{Fore.YELLOW}Cet outil permet de :{Style.RESET_ALL}",
        "  - Supprimer les pages vides.",
        "  - Ajouter un filigrane perso.",
        "  - Paginater les documents.",
        "  - Rendre le sommaire interactif.",
        "  - Gérer les métadonnées.",
        "  - Sécuriser avec des mdp.",
        "  - Signer le PDF (.pfx requis).",
    ]

    # Largeur maximale SANS couleurs
    max_content_width = max(len(strip_ansi(line)) for line in lines)
    total_width = max_content_width + 4

    # Affiche le cadre supérieur
    print(f"{Fore.WHITE}{Style.BRIGHT}╔{'═' * total_width}╗{Style.RESET_ALL}")

    for line in lines:
        visible = strip_ansi(line)
        # Si la ligne est vide
        if not visible:
            print(f"║{' ' * (total_width)}║")
        else:
            padding = total_width - len(visible)
            left = padding // 2 if line in lines[:3] else 1
            right = padding - left if line in lines[:3] else padding - 1
            # Centrer les 3 premières lignes, aligner à gauche les autres
            if line in lines[:3]:
                print(f"║{' ' * left}{line}{' ' * right}║")
            else:
                print(f"║ {line}{' ' * (total_width - 1 - len(visible))}║")

    # Affiche le cadre inférieur
    print(f"{Fore.WHITE}{Style.BRIGHT}╚{'═' * total_width}╝{Style.RESET_ALL}")

def goodbye(ORIGINAL_PDF_NAME):
    save_path = None
    try:
        root = Tk()
        root.withdraw()
        print(f"\n{Fore.MAGENTA}Enregistrement du fichier PDF...{Style.RESET_ALL}")
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=os.path.basename(ORIGINAL_PDF_NAME)
        )
        root.destroy()
    except Exception:
        pass
    if not save_path:
        print(f"{Fore.MAGENTA}Entrer l'emplacement d’enregistrement (ou juste un nom de fichier) :{Style.RESET_ALL}")
        user_input = input(f"{Fore.GREEN}> {Style.RESET_ALL}").strip()
        if user_input:
            if os.path.isdir(user_input):
                save_path = os.path.join(user_input, os.path.basename(TMP_PDF_PATH1))
            else:
                if not user_input.lower().endswith(".pdf"):
                    user_input += ".pdf"
                save_path = os.path.join(RESULTS_PATH, user_input)
        else:
            save_path = os.path.join(RESULTS_PATH, ORIGINAL_PDF_NAME)
    save_path = os.path.abspath(save_path)
    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        shutil.copy(TMP_PDF_PATH1, save_path)
    except Exception as e:
        print(f"{Fore.RED}Erreur : impossible de copier le fichier vers {save_path}. Raison : {e}{Style.RESET_ALL}")
        return
    if not os.path.exists(save_path):
        print(f"{Fore.RED}Erreur : le fichier n’a pas été enregistré à {save_path}{Style.RESET_ALL}")
        return
    os.system("cls" if os.name == "nt" else "clear")
    lines = [
        f"{Fore.MAGENTA}Bienvenue dans l'outil SiyuPDF !{Style.RESET_ALL}",
        f"{Fore.LIGHTBLACK_EX}{'-' * 34}{Style.RESET_ALL}",
        "",
        f"Fichier final enregistré à : {Fore.LIGHTMAGENTA_EX}{save_path}{Style.RESET_ALL}",
        "",
    ]
    max_content_width = max(len(strip_ansi(line)) for line in lines)
    total_width = max_content_width + 4
    print(f"{Fore.WHITE}{Style.BRIGHT}╔{'═' * total_width}╗{Style.RESET_ALL}")
    for line in lines:
        visible = strip_ansi(line)
        if not visible:
            print(f"║{' ' * (total_width)}║")
        else:
            padding = total_width - len(visible)
            left = padding // 2 if line in lines[:2] else 1
            right = padding - left if line in lines[:2] else padding - 1
            if line in lines[:2]:
                print(f"║{' ' * left}{line}{' ' * right}║")
            else:
                print(f"║ {line}{' ' * (total_width - 1 - len(visible))}║")
    print(f"{Fore.WHITE}{Style.BRIGHT}╚{'═' * total_width}╝{Style.RESET_ALL}")

