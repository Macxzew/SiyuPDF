from siyupdf.process import clean_1page, add_watermark, add_footer, clickable_toc, set_metadata, add_password, add_sign
from siyupdf.utils import prepare_env, clean_tmp
from siyupdf.message import welcome, goodbye
from colorama import Fore, Style
from colorama import Fore, init
import sys

# Initialize colorama
init(autoreset=True)


def main():
    """
    Point d'entrée du script. Gère l'importation d'un fichier PDF,
    la création des répertoires et les étapes de traitement.
    """
    # Message de bienvenue
    welcome()
    try:
        # Importation et préparation du fichier
        ORIGINAL_PDF_NAME = prepare_env()
        # Traitement principal
        clean_1page()
        add_watermark()
        add_footer()
        clickable_toc()
        set_metadata(finalize=True)
        add_sign()
        add_password()
        # Message d'au revoir
        goodbye(ORIGINAL_PDF_NAME)
        # Nettoyage des fichiers temporaires
        clean_tmp()
    except Exception as e:
        print(f"{Fore.RED}Une erreur est survenue : {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}Interruption du programme. Fermeture en cours...{Style.RESET_ALL}")
        sys.exit(1)
if __name__ == "__main__":
    main()
