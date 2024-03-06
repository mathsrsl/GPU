import json
from flask import abort
import requests
import warnings
import icalendar
from PIL import Image, ImageDraw, ImageFont
import datetime
from dateutil import parser, tz


def getJSON(username):
    # Ignorer les avertissements liés aux requêtes non sécurisées (SSL)
    warnings.filterwarnings("ignore", category=requests.packages.urllib3.exceptions.InsecureRequestWarning)


    response = requests.get("https://iut-ical.unice.fr/gpucal.php?name=" + username, verify=False)

    if response.status_code != 200:
        abort(500)  # internal server error

    ical_string = response.content

    # parse icalendar string
    calendar = icalendar.Calendar.from_ical(ical_string)
    # convert calendar to JSON
    id = 0
    events = []
    for component in calendar.walk():
        if component.name == "VEVENT":
            event = {
                "id": id,
                "summary": component.get("summary").to_ical().decode(),
                "location": component.get("location").to_ical().decode(),
                "description": component.get("description").to_ical().decode(),
                "start_time": component.get("dtstart").dt.isoformat(),
                "end_time": component.get("dtend").dt.isoformat(),
            }
            events.append(event)
            id += 1

    # Ajout de l'username dans le JSON
    events.append({"username": username})

    events_json = json.dumps(events)

    return events_json



def createEDT(json_data, semaine=None, save=False):
    """
    Crée une image de l'emploi du temps à partir du JSON fourni
    :param json_data: JSON contenant les événements
    :param semaine: Numéro de la semaine, Si non spécifié, la semaine actuelle sera utilisée, Si 'Next', la semaine suivante sera utilisée
    :param save: Booléen, Si True, l'image sera enregistrée
    """

    import datetime

    # Vérification de la semaine
    if semaine is None:
        semaine = datetime.date.today().isocalendar()[1]
    elif semaine == "next":
        semaine = datetime.date.today().isocalendar()[1] + 1
    else:
        semaine = int(semaine)


    # Vérification du numéro de l'anée en fonction de la semaine passée en paramètre
    if semaine < 36:
        annee = datetime.date.today().year
    else:
        annee = datetime.date.today().year + 1

    from datetime import datetime, timedelta

    # ----------------------------------------------
    # Initialisation

    data = json.loads(json_data)

    # Jours de la semaine
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Définir des couleurs pour des cours spécifiques
    course_colors = {
        'R2.01': (255, 204, 204),
        'R2.02': (204, 255, 204),
        'R2.03': (204, 204, 255),
        'R2.04': (255, 204, 255),
        'R2.05': (204, 255, 255),
        'R2.06': (255, 255, 204),
        'R2.07': (255, 204, 153),
        'R2.08': (204, 153, 255),
        'R2.09': (255, 153, 204),
        'R2.10': (153, 204, 255),
        'R2.11': (255, 204, 102),
        'R2.12': (204, 102, 255),
        'R2.13': (255, 102, 204),
        'R2.14': (102, 204, 255),
        'S2.01': (255, 255, 153),
        'S2.03': (255, 153, 255),
        'S2.05': (153, 255, 255),
        'Unknown': (200, 200, 200)  # Couleur pour les cours inconnus
    }

    # Création de l'image et des paramètres de dessin
    img_width = 620
    img_height = 600
    background_color = (255, 255, 255)
    text_color = (0, 0, 0)
    font_size = 10

    img = Image.new('RGB', (img_width, img_height), background_color)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("arial.ttf", font_size)

    img_width = 600 # Ne pas compter la marche à droite

    # ----------------------------------------------
    # Affichage du titre


    first_day = datetime.strptime(f"{annee}-{semaine}-1", "%Y-%W-%w") # Obtenir le premier jour de la semaine
    last_day = first_day + timedelta(days=6) # Obtenir le dernier jour de la semaine

    # Formatez les dates dans le format dd/mm
    title_text = f"Semaine {semaine}, du {first_day.strftime('%d/%m')} au {last_day.strftime('%d/%m')} - fait le {datetime.now().strftime('%d/%m/%Y')} à {datetime.now().strftime('%H:%M')}"
    #title_text = f"Semaine {semaine}, du {first_day.strftime('%d/%m')} au {last_day.strftime('%d/%m')} - fait le {datetime.now().strftime('%d/%m/%Y')} à {(datetime.now() + timedelta(hours=1)).strftime('%H:%M')}"

    title_font = ImageFont.truetype("arial.ttf", 16)  # Taille de police plus grande pour le titre

    # Créer une boîte englobante pour le titre
    title_bbox = draw.textbbox((0, 0), title_text, font=title_font)

    # Cacluler la position du titre et le dessiner
    title_width = title_bbox[2] - title_bbox[0]  # Cacluler la largeur de la boîte englobante
    title_x = (img_width - title_width) // 2
    draw.text((title_x, 15), title_text, text_color, font=title_font)

    # ----------------------------------------------
    # Affichage du footer

    # Afficher le nom d'utilisateur
    username = data.pop()["username"]
    footer_text = f"basé sur l'utilisateur : {username}"
    footer_font = ImageFont.truetype("arial.ttf", 9)
    draw.text((5, img_height - 15), footer_text, text_color, font=footer_font)

    # Affichage de l'auteur
    footer_text = f"by @kayu"
    draw.text((img_width - 50, img_height - 15), footer_text, text_color, font=footer_font)


    # ----------------------------------------------
    # Dessiner les jours de la semaine et les heures (base de l'emploi du temps)

    # Dessiner les jours de la semaine
    for i, day in enumerate(days_of_week):
        day_x = i * (img_width // len(days_of_week) - 10) + 90
        draw.text((day_x, 60), day, text_color, font=font)

    # Dessiner les heures
    for i in range(8, 19):
        hour_y = (i - 7) * (img_height // 13) + 50
        draw.text((5, hour_y), f'{i:02}:00', text_color, font=font)

        # Déssiner les lignes horizontales à 8h, 9h, 10h, 11h, 12h, 13h, 14h, 15h, 16h, 17h
        draw.line([(60, hour_y+5), (img_width - 20, hour_y+5)], fill=(0, 0, 0), width=1)
        if i == 13:
            # Afficher "C'est de l'heure de la graille"
            draw.text((270, hour_y-10), "C'est l'heure de la graille", text_color, font=font)

    # ----------------------------------------------
    # Dessiner les événements avec informations détaillée

    for entry in data:
        start_time = parser.parse(entry["start_time"]).replace(tzinfo=tz.tzutc())
        end_time = parser.parse(entry["end_time"]).replace(tzinfo=tz.tzutc())

        if start_time.isocalendar()[1] != semaine and end_time.isocalendar()[1] != semaine:
            continue

        day_index = start_time.weekday()
        start_hour = start_time.hour - 8
        end_hour = end_time.hour - 8

        course_color = course_colors.get(entry["description"].split()[-1].strip("()"), course_colors["Unknown"])

        event_x = day_index * (img_width // len(days_of_week) - 10) + 50

        event_y_start = start_hour * (img_height // 13) + int(
            start_time.minute / 60 * (img_height // 13)) + 101
        event_y_end = end_hour * (img_height // 13) + int(
            end_time.minute / 60 * (img_height // 13)) + 101

        draw.rectangle([(event_x, event_y_start), (event_x + (img_width // len(days_of_week) - 10), event_y_end)],
                       fill=course_color, outline=(0, 0, 0))

        if entry["description"].split()[-1].strip("()") in course_colors:
            ressource = entry["description"].split()[-1].strip("()")
        else:
            ressource = "N/A"

        coursProf = " ".join(entry["summary"].split()[-2:])
        salle = entry["location"]
        horraire = f"{datetime.fromisoformat(entry['start_time']).strftime('%H:%M')} - {datetime.fromisoformat(entry['end_time']).strftime('%H:%M')}"


        # Si dure entre 30 minutes (inclus) et 1 heure (exclus)
        if end_time - start_time < timedelta(hours=1) and end_time - start_time >= timedelta(minutes=30):
            draw.text((event_x + 5, event_y_start + 5),
                      f"{horraire} | {ressource}",
                      text_color, font=font)
        # Si dure 1h ou plus
        if end_time - start_time >= timedelta(hours=1):
            draw.text((event_x + 5, event_y_start + 5),
                      f"{horraire} | {ressource}\n{coursProf}\n{salle}",
                      text_color, font=font)

            if end_time - start_time >= timedelta(hours=1, minutes=30):
                if coursProf.split()[0] == "_DS":
                    draw.text((event_x + 5, event_y_start + 5),
                              f"\n\n\nBon courage !",
                              (10, 10, 10), font=font)

            if end_time - start_time >= timedelta(hours=2) and coursProf.split()[0] != "_DS":
                if coursProf.split()[-1] == "acundege":
                    draw.text((event_x + 5, event_y_start + 5),
                              f"\n\n\n\nAlors les tables\nde karnaugh",
                              (10, 10, 10), font=font)

                if coursProf.split()[-1] == "dbojovic":
                    draw.text((event_x + 5, event_y_start + 5),
                              f"\n\n\n\nAttention les oreilles",
                              (10, 10, 10), font=font)

                if coursProf.split()[-1] == "fmognol":
                    draw.text((event_x + 5, event_y_start + 5),
                              f"\n\n\n\nDura lex, sed lex",
                              (10, 10, 10), font=font)

                if coursProf.split()[-1] == "courtois":
                    draw.text((event_x + 5, event_y_start + 5),
                              f"\n\n\n\nCarrefour",
                              (10, 10, 10), font=font)

                if coursProf.split()[-1] == "sarmient":
                    draw.text((event_x + 5, event_y_start + 5),
                              f"\n\n\n\nLe goat",
                              (10, 10, 10), font=font)

                if coursProf.split()[-1] == "_NE":
                    draw.text((event_x + 5, event_y_start + 5),
                              f"\n\n\n\nChomage",
                              (10, 10, 10), font=font)

                if coursProf.split()[-1] == "pourcelo":
                    draw.text((event_x + 5, event_y_start + 5),
                              f"\n\n\n\nAlors ? Ca Wims ?",
                              (10, 10, 10), font=font)

                if coursProf.split()[-1] == "rey":
                    draw.text((event_x + 5, event_y_start + 5),
                              f"\n\n\n\nLa rey-cursivité",
                              (10, 10, 10), font=font)

                if coursProf.split()[-1] == "bilancin":
                    draw.text((event_x + 5, event_y_start + 5),
                              f"\n\n\n\nGilou",
                              (10, 10, 10), font=font)


    # Remettre le nom d'utilisateur dans le JSON
    data.append({"username": username})

    if save:
        img.save(f"export/EDT_{username}_{semaine}.png")
    img.show()


def isHollidays(json_data, semaine=None):
    """
    Vérifie si l'utilisateur a des cours pendant la semaine spécifiée
    Returne True si l'utilisateur n'a pas de cours pendant la semaine spécifiée, False sinon
    :param json_data: Le JSON contenant les événements
    :param semaine: Si non spécifié, la semaine actuelle sera utilisée, Si 'Next', la semaine suivante sera utilisée, Sinon, le numéro de la semaine spécifié sera utilisé
    :return: Booléen
    """

    if semaine is None:
        semaine = datetime.date.today().isocalendar()[1]
    elif semaine == "next":
        semaine = datetime.date.today().isocalendar()[1] + 1
    else:
        semaine = int(semaine)

    data = json.loads(json_data)

    for entry in data:
        # Vérifier si les clés nécessaires existent dans l'entrée
        if "start_time" in entry and "end_time" in entry:
            start_time = parser.parse(entry["start_time"]).replace(tzinfo=tz.tzutc())
            end_time = parser.parse(entry["end_time"]).replace(tzinfo=tz.tzutc())

            if start_time.isocalendar()[1] == semaine or end_time.isocalendar()[1] == semaine:
                return False

    return True


def getWeekCourses(json_data, semaine="None"):
    """
    Récupère les cours du JSON pour la semaine spécifiée
    :param json_data: JSON
    :param semaine: Si non spécifié, la semaine actuelle sera utilisée, Si 'Next', la semaine suivante sera utilisée, Sinon, le numéro de la semaine spécifié sera utilisé
    :return: Liste des cours pour la semaine spécifiée
    """

    if semaine is None:
        semaine = datetime.date.today().isocalendar()[1]
    elif semaine == "next":
        semaine = datetime.date.today().isocalendar()[1] + 1
    else:
        semaine = int(semaine)

    data = json.loads(json_data)
    semaine_courses = []

    for entry in data:
        if "start_time" in entry and "end_time" in entry:
            start_time = parser.parse(entry["start_time"]).replace(tzinfo=tz.tzutc())
            end_time = parser.parse(entry["end_time"]).replace(tzinfo=tz.tzutc())

            if start_time.isocalendar()[1] == semaine or end_time.isocalendar()[1] == semaine:
                semaine_courses.append(entry)

    return semaine_courses


def isEqual(json_data1, json_data2, semaine=None):
    """
    Vérifie si deux versions de l'emploi du temps sont identiques pour la semaine spécifiée
    :param json_data1: JSON 1
    :param json_data2: JSON 2
    :param semaine: Si non spécifié, la semaine actuelle sera utilisée, Si 'Next', la semaine suivante sera utilisée, Sinon, le numéro de la semaine spécifié sera utilisé
    :return: Booléen
    """

    if semaine is None:
        semaine = datetime.date.today().isocalendar()[1]
    elif semaine == "next":
        semaine = datetime.date.today().isocalendar()[1] + 1
    else:
        semaine = int(semaine)

    courses1 = getWeekCourses(json_data1, semaine)
    courses2 = getWeekCourses(json_data2, semaine)

    isEqual = True

    if len(courses1) != len(courses2):
        isEqual = False
    else:
        for entry1 in courses1:
            if not any(entry1 == entry2 for entry2 in courses2):
                isEqual = False
                break

    return isEqual






username = input("Entrer un nom d'utilisateur : ")
semaineInput = input("Entrer un numéro de semaine : ('n' pour la semaine suivante, 'a' pour la semaine actuelle, ou un numéro de semaine) : ")
dlChoice = input("Voulez-vous enregistrer l'image ? (o/n) : ")


print("Génération en cours...")
print("Veuillez patienter...")

json_string = getJSON(username) # Récupérer la chaîne JSON
json_list = json.loads(json_string) # Charger la chaîne JSON en tant que liste Python

# Générer l'emploi du temps
if semaineInput == "a":
    if dlChoice.lower() == "o":
        createEDT(json_string, save=True)
    else:
        createEDT(json_string)
elif semaineInput == "n":
    if dlChoice.lower() == "o":
        createEDT(json_string, "next", save=True)
    else:
        createEDT(json_string, "next")
else:
    if dlChoice.lower() == "o":
        createEDT(json_string, semaineInput, save=True)
    else:
        createEDT(json_string, semaineInput)




