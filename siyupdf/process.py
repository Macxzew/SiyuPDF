import tkinter as tk
import unicodedata
import datetime
import getpass
import hashlib
import secrets
import pikepdf
import shutil
import string
import pytz
import fitz
import re
import os

from siyupdf.config import TMP_PDF_PATH1, TMP_PDF_PATH2, TMP_WATERMARK_PATH, FONT_PATH
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.asymmetric import padding
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import letter
from siyupdf.utils import animated_status
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from colorama import Fore, Style
from asn1crypto import cms, x509
from tkinter import filedialog
from io import BytesIO


def clean_1page():
    """
    Supprime la première page du PDF si elle est vide ou ne contient aucun contenu significatif.
    Modifie directement TMP_PDF_PATH.
    """
    print(f"\n{Fore.YELLOW}Étape 1 : Suppression de la première page si vide")
    animated_status("Traitement en cours")
    doc = fitz.open(TMP_PDF_PATH1)
    if doc.page_count > 0:
        first_page = doc.load_page(0)
        text_instances = first_page.get_text("dict")
        if text_instances["blocks"]:
            significant_text = any(
                block["lines"] and block["bbox"][1] <= 750
                for block in text_instances["blocks"]
                if block.get("lines")
            )
            if not significant_text:
                doc.delete_page(0)
    doc.save(TMP_PDF_PATH2, incremental=False)


def add_watermark():
    """
    Crée un filigrane et l'applique directement sur TMP_PDF_PATH.
    """
    print(f"{Fore.YELLOW}Étape 2 : Ajout d'un filigrane {Style.RESET_ALL}")
    response = input(f"{Fore.MAGENTA}- Voulez-vous créer un filigrane ? (y/N): {Style.RESET_ALL}").strip().lower()
    if response.startswith('y'):
        watermark_text = input(f"{Fore.MAGENTA}- Entrez un texte pour le filigrane (défaut = 'Watermarked') : {Style.RESET_ALL}").strip()
        watermark_text = watermark_text if watermark_text else "Watermarked"

        # Créer l'image du filigrane
        width, height = 500, 500
        image = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(FONT_PATH, 36)
        text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (width - text_width) / 2
        y = (height - text_height) / 2
        draw.text((x, y), watermark_text, font=font, fill=(100, 100, 100, 128))
        image = image.rotate(45, expand=1)
        image.save(TMP_WATERMARK_PATH, format="PNG")

        # Appliquer le filigrane au PDF
        reader = PdfReader(TMP_PDF_PATH2)
        writer = PdfWriter()
        with BytesIO() as packet:
            c = canvas.Canvas(packet, pagesize=letter)
            c.drawImage(TMP_WATERMARK_PATH, 0, 0, width=letter[0], height=letter[1], mask="auto")
            c.save()
            packet.seek(0)
            overlay_page = PdfReader(packet).pages[0]
            for page in reader.pages:
                page.merge_page(overlay_page)
                writer.add_page(page)
        # Sauvegarder les changements dans TMP_PDF_PATH
        with open(TMP_PDF_PATH2, "wb") as output_pdf:
            writer.write(output_pdf)
        animated_status("Traitement en cours")
    else:
        print(f"{Fore.LIGHTBLACK_EX}Création de filigrane (SKIP).")


def add_footer():
    """
    Ajoute des pieds de page au fichier temporaire TMP_PDF_PATH.
    """
    print(f"{Fore.YELLOW}Étape 3 : Ajout des pieds de page")
    animated_status("Traitement en cours")
    reader = PdfReader(TMP_PDF_PATH2)
    writer = PdfWriter()
    footer_height = 23
    for page_number, page in enumerate(reader.pages):
        media_box = page.mediabox
        temp_stream = BytesIO()
        page_width = float(media_box[2])
        page_height = float(media_box[3])
        temp_canvas = canvas.Canvas(temp_stream, pagesize=(page_width, page_height))
        temp_canvas.setFillColorRGB(1, 1, 1)
        temp_canvas.rect(0, 0, page_width, footer_height, stroke=0, fill=1)
        temp_canvas.setFillColorRGB(0, 0, 0)
        footer_text = f"{page_number + 1} / {len(reader.pages)}"
        temp_canvas.drawCentredString(page_width / 2, footer_height / 2, footer_text)
        temp_canvas.save()
        temp_stream.seek(0)
        overlay_page = PdfReader(temp_stream).pages[0]
        page.merge_page(overlay_page)
        writer.add_page(page)
    # Sauvegarder dans TMP_PDF_PATH
    with open(TMP_PDF_PATH1, "wb") as f:
        writer.write(f)


def clickable_toc():
    """
    Recherche la page du sommaire dans le PDF et ajoute des liens cliquables
    invisibles sur toute la ligne pour chaque référence de page trouvée.
    Gère également les sommaires sur plusieurs pages identifiées par des lignes de points.
    """
    print(f"{Fore.YELLOW}Étape 4 : Rendre le sommaire redirigeable")
    animated_status("Traitement en cours")
    doc = fitz.open(TMP_PDF_PATH1)
    toc_pages = []
    # Liste des titres de sommaire acceptés
    toc_titles = [
        "📖 Sommaire", "Sommaire", "Contents",
        "Table of Contents", "Table des matières"
    ]
    # Étape 1 : Trouver la première page du sommaire
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        normalized_text = unicodedata.normalize('NFKD', text).replace('\n', ' ').strip()
        if any(title in normalized_text for title in toc_titles):
            toc_pages.append(page_num)
            break
    else:
        print("Page du sommaire non trouvée.")
        doc.close()
        return
    # Étape 2 : Vérifier les pages suivantes pour des continuations du sommaire
    current_page = toc_pages[-1]
    while current_page + 1 < doc.page_count:
        next_page = current_page + 1
        page = doc.load_page(next_page)
        text = page.get_text("text")
        lines = text.split('\n')
        # Vérifier si une ligne contient ".................." (signifiant une continuation du sommaire)
        has_dots = any(".................." in line for line in lines)
        if has_dots:
            toc_pages.append(next_page)
            current_page = next_page
        else:
            break  # Plus de pages de sommaire détectées
    if not toc_pages:
        print("Aucune page de sommaire supplémentaire détectée.")
    # Étape 3 : Pour chaque page du sommaire, ajouter les liens cliquables
    pattern = r"Page\s+(\d+)"
    for toc_page_num in toc_pages:
        toc_page = doc.load_page(toc_page_num)
        blocks = toc_page.get_text("blocks")
        for block in blocks:
            block_text = unicodedata.normalize('NFKD', block[4]).replace('\n', ' ').strip()
            for match in re.finditer(pattern, block_text):
                try:
                    page_number = int(match.group(1)) - 1  # Convertir en index 0
                except ValueError:
                    continue  # Ignorer si ce n'est pas un nombre valide
                if 0 <= page_number < doc.page_count:
                    x0, y0, x1, y1 = block[:4]
                    rect = fitz.Rect(x0, y0, x1, y1)
                    toc_page.insert_link({
                        "kind": fitz.LINK_GOTO,
                        "from": rect,
                        "page": page_number
                    })
    # Étape 4 : Sauvegarder les modifications
    doc.saveIncr()
    doc.close()


def set_metadata(finalize=False):
    """
    Gère les métadonnées d'un fichier PDF.
    """
    if not finalize:
        return
    print(f"{Fore.YELLOW}Étape 5 : Gestion des métadonnées{Style.RESET_ALL}")
    # Vérifier si l'utilisateur souhaite personnaliser les métadonnées
    user_choice = input(f"{Fore.MAGENTA}- Voulez-vous personnaliser les métadonnées ? (y/N) : {Style.RESET_ALL}").strip().lower()
    with pikepdf.open(TMP_PDF_PATH1, allow_overwriting_input=True) as pdf:
        # Effacement complet des métadonnées
        title = ""
        author = ""
        with pdf.open_metadata() as metadata:
            metadata.clear()
            # Si personnalisation souhaitée, récupérer les entrées utilisateur
            if user_choice == "y":
                title = input(
                    f"{Fore.MAGENTA}- Entrez le titre du document : {Style.RESET_ALL}"
                ).strip()
                author = input(
                    f"{Fore.MAGENTA}- Entrez l'auteur du document : {Style.RESET_ALL}"
                ).strip()
                if title:
                    metadata["dc:title"] = title
                if author:
                    metadata["dc:creator"] = [author]
        # Supprimer toutes les clés de docinfo une par une
        for key in list(pdf.docinfo.keys()):
            del pdf.docinfo[key]
        # Supprimer complètement les métadonnées XMP si elles existent
        if "/Metadata" in pdf.Root:
            del pdf.Root["/Metadata"]
        # Supprimer les traces spécifiques aux dates
        if "CreationDate" in pdf.docinfo:
            del pdf.docinfo["CreationDate"]
        if "ModDate" in pdf.docinfo:
            del pdf.docinfo["ModDate"]
        # Définir les métadonnées standard dans docinfo
        if title:
            pdf.docinfo["/Title"] = title
        if author:
            pdf.docinfo["/Author"] = author
        if "/Producer" in pdf.docinfo:
            del pdf.docinfo["/Producer"]
        # Sauvegarder directement les modifications dans un fichier temporaire
        pdf.save(TMP_PDF_PATH1)
    # Remplacer le fichier d'origine par le fichier temporaire
    animated_status("Traitement en cours")


def add_sign():
    """
    Ajoute une signature numérique au fichier PDF temporaire TMP_PDF_PATH1.
    """
    print(f"{Fore.YELLOW}Étape 6 : Ajout d'une signature numérique{Style.RESET_ALL}")
    user_choice = input(
        f"{Fore.MAGENTA}- Voulez-vous signer le PDF numériquement ? (y/N) : {Style.RESET_ALL}"
    ).strip().lower()
    if user_choice != 'y':
        print(f"{Fore.LIGHTBLACK_EX}Signature numérique (SKIP).{Style.RESET_ALL}")
        return
    cert_data = None
    try:
        print(f"{Fore.MAGENTA}- Importation du certificat (.pfx)...{Style.RESET_ALL}")
        root = tk.Tk()
        root.withdraw()
        cert_path = filedialog.askopenfilename(
            title="Sélectionnez le fichier de certificat (.pfx)",
            filetypes=[("Fichiers PFX", "*.pfx"), ("Tous les fichiers", "*.*")]
        )
        if not cert_path:
            raise FileNotFoundError("Aucun fichier sélectionné.")
        cert_path = os.path.abspath(cert_path)
        with open(cert_path, 'rb') as f:
            cert_data = f.read()
    except Exception as e:
        print(f"{Fore.RED}Erreur lors de l'importation du certificat : {e}{Style.RESET_ALL}")
        return
    cert_password = getpass.getpass(
        f"{Fore.MAGENTA}- Mot de passe du certificat : {Style.RESET_ALL}"
    ).strip()
    try:
        private_key, cert, additional_certs = pkcs12.load_key_and_certificates(
            cert_data, cert_password.encode()
        )
        if not private_key or not cert:
            raise ValueError(
                "La clé privée ou le certificat principal n'ont pas été chargés correctement."
            )
        cert_asn1 = x509.Certificate.load(cert.public_bytes(serialization.Encoding.DER))
        additional_asn1_certs = [
            x509.Certificate.load(c.public_bytes(serialization.Encoding.DER))
            for c in additional_certs or []
        ]
        certificates = [
            cms.CertificateChoices({'certificate': cert_asn1})
        ] + [
            cms.CertificateChoices({'certificate': c}) for c in additional_asn1_certs
        ]
        if not os.path.isfile(TMP_PDF_PATH1):
            raise FileNotFoundError(f"Le fichier PDF spécifié n'existe pas : {TMP_PDF_PATH1}")

        with open(TMP_PDF_PATH1, 'rb') as pdf_file:
            pdf_data = pdf_file.read()
        if b"/ByteRange" not in pdf_data or b"/Contents" not in pdf_data:
            placeholder = b"/ByteRange [0 0 0 0] /Contents <" + b"0" * 8192 + b">"
            pdf_data += placeholder

        if b"/ByteRange" not in pdf_data or b"/Contents" not in pdf_data:
            raise ValueError("Échec de l'ajout des champs nécessaires au fichier PDF.")

        digest = hashlib.sha256(pdf_data).digest()

        signature = private_key.sign(
            digest,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        timestamp = datetime.datetime.now().isoformat()
        signed_data = cms.SignedData({
            'version': 'v1',
            'digest_algorithms': [cms.DigestAlgorithm({'algorithm': 'sha256'})],
            'encap_content_info': cms.ContentInfo({
                'content_type': 'data',
                'content': None
            }),
            'certificates': certificates,
            'signer_infos': [cms.SignerInfo({
                'version': 'v1',
                'sid': cms.SignerIdentifier({
                    'issuer_and_serial_number': cms.IssuerAndSerialNumber({
                        'issuer': cert_asn1.issuer,
                        'serial_number': cert_asn1.serial_number
                    })
                }),
                'digest_algorithm': cms.DigestAlgorithm({'algorithm': 'sha256'}),
                'signed_attrs': [
                    cms.CMSAttribute({
                        'type': 'content_type',
                        'values': ['data']
                    }),
                    cms.CMSAttribute({
                        'type': 'signing_time',
                        'values': [cms.Time({
                            'utc_time': datetime.datetime.now(pytz.utc)
                        })]
                    }),
                    cms.CMSAttribute({
                        'type': 'message_digest',
                        'values': [hashlib.sha256(pdf_data).digest()]
                    })
                ],
                'signature_algorithm': cms.SignedDigestAlgorithm({'algorithm': 'rsassa_pkcs1v15'}),
                'signature': signature
            })]
        })
        pkcs7_signature = cms.ContentInfo({
            'content_type': 'signed_data',
            'content': signed_data
        }).dump()
        byte_range_start = pdf_data.find(b"/ByteRange [")
        if byte_range_start == -1:
            raise ValueError("Impossible de trouver /ByteRange dans le PDF.")
        byte_range_end = pdf_data.find(b">", byte_range_start) + 1
        byte_range_values = [0, byte_range_start, len(pdf_data) - 8192, 8192]
        byte_range_string = f"[{byte_range_values[0]} {byte_range_values[1]} {byte_range_values[2]} {byte_range_values[3]}]".encode()
        pdf_data = (
            pdf_data[:byte_range_start] +
            b"/ByteRange " +
            byte_range_string +
            pdf_data[byte_range_end:]
        )
        # Remplace le placeholder avec la signature PKCS#7
        pdf_data = pdf_data.replace(b"0" * 8192, pkcs7_signature)
        if b"/ByteRange" not in pdf_data or b"/Contents" not in pdf_data:
            raise ValueError("Erreur lors de la génération des champs de signature dans le PDF.")
        # Écriture du fichier signé
        with open(TMP_PDF_PATH1, 'wb') as output_file:
            output_file.write(pdf_data)
        animated_status("Traitement en cours")
    except FileNotFoundError:
        print(f"{Fore.RED}Erreur lors de la signature.{Style.RESET_ALL}")
    except ValueError as e:
        print(f"{Fore.RED}Erreur lors de la signature : {e}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Erreur inattendue : {e}{Style.RESET_ALL}")




def add_password():
    """
    Sécurise le PDF avec des restrictions empêchant la modification et l'annotation.
    """
    print(f"{Fore.YELLOW}Étape 7 : Sécurisation du PDF avec des restrictions{Style.RESET_ALL}")
    # Demander à l'utilisateur s'il souhaite définir des mots de passe
    response = input(f"{Fore.MAGENTA}- Voulez-vous sécuriser le PDF avec des mots de passe ? (y/N) : {Style.RESET_ALL}").strip().lower()
    # Initialisation des mots de passe
    user_password = ""
    owner_password = ""
    if response.startswith('y'):
        # Demander le mot de passe utilisateur
        user_password = input(f"{Fore.MAGENTA}- Mdp pour lire le PDF (vide pour aucun, active le chiffrement) : {Style.RESET_ALL}").strip()
        # Demander le mot de passe propriétaire
        owner_password = input(f"{Fore.MAGENTA}- Mdp pour modifier le PDF (vide pour un mdp aléatoire, non récupérable) : {Style.RESET_ALL}").strip()
        if not owner_password:
            # Générer un mot de passe propriétaire aléatoire
            owner_password_length = 20
            characters = string.ascii_letters + string.digits + string.punctuation
            owner_password = ''.join(secrets.choice(characters) for _ in range(owner_password_length))
    else:
        print(f"{Fore.MAGENTA}- Aucun mot de passe utilisateur défini, un mot de passe vide sera utilisé (chiffrement activé).{Style.RESET_ALL}")
        user_password = ""  # Mot de passe utilisateur vide pour activer le chiffrement
        # Générer un mot de passe propriétaire aléatoire
        owner_password_length = 20
        characters = string.ascii_letters + string.digits + string.punctuation
        owner_password = ''.join(secrets.choice(characters) for _ in range(owner_password_length))
    try:
        # Définir le chemin temporaire pour le fichier sécurisé
        TEMP_PASSWORD_PROTECTED = TMP_PDF_PATH2
        # Configurer les permissions pour empêcher la modification et l'annotation
        permissions = pikepdf.Permissions(
            accessibility=False,       # Empêche l'accès via des technologies d'assistance
            extract=True,              # Autorise l'extraction de contenu (clic droit + copier)
            modify_annotation=False,   # Empêche la modification des annotations
            modify_assembly=False,     # Empêche l'assemblage ou la réorganisation des pages
            modify_form=False,         # Empêche de remplir des formulaires
            modify_other=False,        # Empêche toute autre modification du document
            print_lowres=True,         # Autorise l'impression en basse qualité
            print_highres=True         # Autorise l'impression en haute qualité
        )
        # Appliquer le chiffrement avec les mots de passe et les permissions définis
        with pikepdf.open(TMP_PDF_PATH1) as pdf:
            pdf.save(
                TEMP_PASSWORD_PROTECTED,
                encryption=pikepdf.Encryption(
                    user=user_password,    # Mot de passe utilisateur (vide si non défini)
                    owner=owner_password,  # Mot de passe propriétaire
                    allow=permissions,     # Appliquer les permissions définies
                    R=6                    # Révision pour AES-256
                )
            )
        # Remplacer le fichier original par le fichier sécurisé
        shutil.move(TEMP_PASSWORD_PROTECTED, TMP_PDF_PATH1)
    except pikepdf.PdfError as e:
        print(f"{Fore.RED}Erreur lors de la sécurisation du PDF : {e}{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}Erreur lors de la sécurisation du PDF : {e}{Style.RESET_ALL}")
    animated_status("Traitement en cours")
