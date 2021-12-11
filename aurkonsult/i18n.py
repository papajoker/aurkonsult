"""
translations
"""
import gettext

__LANG_USER__ = ""


def set_lang(lg):
    global __LANG_USER__
    __LANG_USER__ = lg


'''
def gettext_gettext(string: str) -> str:
    """ translate texte if in dico"""
    lang = __LANG_USER__
    traductions = {
        "Exit": {
            "FR": "Quitter",
        },
        "Update": {
            "FR": "Mettre à jour",
        },
        "New packages": {
            "FR": "Nouveaux paquets",
        },
        "Check my aur packages": {
            "FR": "Contrôler les paquets étrangers",
        },
        "Packages": {
            "FR": "Paquets",
        },
        "Info": {
            "FR": "Information",
        },
        "Check local packages": {
            "FR": "Contrôle des paquets étrangers",
        },
        "Search": {
            "FR": "Rechercher",
        },
        "Filter": {
            "FR": "Filtre",
        },
        "Dependencies": {
            "FR": "Dépendances:",
        },
        "Package name": {
            "FR": "Nom du paquet",
        },
        "Package name and Description": {
            "FR": "Nom ou description du paquet",
        },
        "Return": {
            "FR": "Retour",
        },
        "Load": {
            "FR": "Charger",
        },
        "Can load": {
            "FR": "Peut télécharger",
        },
        "Name": {
            "FR": "Nom",
        },
        "Last Modified": {
            "FR": "Dernière mise à jour",
        },
        "First Submitted": {
            "FR": "Première soumission",
        },
        "Url project": {
            "FR": "Adresse web du projet",
        },
        "Maintainer": {
            "FR": "Mainteneur",
        },
        "Popularity": {
            "FR": "Popularité",
        },
        "Make Dependencies": {
            "FR": "Dépendances de construction",
        },
        "Provide": {
            "FR": "Fournit",
        },
        "Comments": {
            "FR": "Commentaires",
        },
        "History": {
            "FR": "Historique",
        },
        "Get History": {
            "FR": "télécharger l'historique",
        },
        "package Informations": {
            "FR": "Informations sur le paquet",
        },
        "Open browser": {
            "FR": "Ouvrir le navigateur web",
        },
        "Do you want go to this url": {
            "FR": "Vous désirez aller à cette adresse web",
        },
        "Install in Konsole": {
            "FR": "Installer via konsole",
        },
        "AUR list": {
            "FR": "AUR exploration",
        },
        "OK new version": {
            "FR": "Nouvelle version installée",
        },
        "End Update": {
            "FR": "Mise à jour terminée",
        },
        "No new database available": {
            "FR": "pas de mise à jour disponible",
        },
        "Changes will be effective after reloading": {
            "FR": "Changements au prochain redémarrage",
        },
        "Extend Database": {
            "FR": "Base de donnée étendue",
        },
        "with dependencies": {
            "FR": "Avec dépendances",
        },
        "user home cache": {
            "FR": "Cache utilisateur dans home",
        },
        "Propose app for install": {
            "FR": "Application pour installer",
        },
        "Save Database in": {
            "FR": "Sauvegarder la base de donnée vers",
        },
        "Save this config": {
            "FR": "Sauvegarder ces préférences",
        },
    }
    if key := traductions.get(string, {}):
        if trad := key.get(lang, ""):
            return trad
    return string


_ = gettext_gettext
'''

gettext.textdomain("aurkonsult")
_ = gettext.gettext
