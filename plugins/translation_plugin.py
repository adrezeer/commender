"""Arabic, English, and French command aliases for DCMDS."""

import json
from pathlib import Path


SETTINGS_PATH = Path(__file__).with_name("translation_settings.json")
LANGUAGES = {
    "ar": "العربية",
    "en": "English",
    "fr": "Français",
    "arabic": "العربية",
    "english": "English",
    "french": "Français",
}
LANGUAGE_CODES = {
    "ar": "ar",
    "arabic": "ar",
    "العربية": "ar",
    "en": "en",
    "english": "en",
    "الانجليزية": "en",
    "fr": "fr",
    "french": "fr",
    "français": "fr",
    "الفرنسية": "fr",
}
ALIASES = {
    "مساعدة": "help",
    "aide": "help",
    "خروج": "exit",
    "quitter": "exit",
    "جديد": "new",
    "nouveau": "new",
    "حالة": "kza",
    "statut": "kza",
    "مسار": "pwd",
    "chemin": "pwd",
    "قائمة": "ls",
    "liste": "ls",
    "بحث": "search",
    "recherche": "search",
    "سجل": "history",
    "historique": "history",
    "مهام": "tasks",
    "tâches": "tasks",
    "إشارة": "bookmark",
    "signet": "bookmark",
    "ترجمة": "translate",
    "traduire": "translate",
}


def load_settings():
    try:
        with SETTINGS_PATH.open("r", encoding="utf-8") as settings_file:
            settings = json.load(settings_file)
        if settings.get("language") in {"ar", "en", "fr"}:
            return settings
    except (OSError, json.JSONDecodeError):
        pass
    return {"language": "ar"}


def save_settings(settings):
    with SETTINGS_PATH.open("w", encoding="utf-8") as settings_file:
        json.dump(settings, settings_file, ensure_ascii=False, indent=2)


def message(language, arabic, english, french):
    return {"ar": arabic, "en": english, "fr": french}[language]


def translate(args, raw_cmd):
    settings = load_settings()
    language = settings["language"]
    action = args[0].lower() if args else "status"

    if action in {"status", "حالة", "statut"}:
        print(message(
            language,
            f"لغة الإضافة الحالية: {LANGUAGES[language]}",
            f"Current plugin language: {LANGUAGES[language]}",
            f"Langue actuelle du plugin : {LANGUAGES[language]}",
        ))
        return

    if action in {"set", "ضبط", "définir"}:
        if len(args) != 2 or args[1].lower() not in LANGUAGE_CODES:
            print(message(
                language,
                "الاستخدام: translate set ar | en | fr",
                "Usage: translate set ar | en | fr",
                "Utilisation : translate set ar | en | fr",
            ))
            return
        language = LANGUAGE_CODES[args[1].lower()]
        save_settings({"language": language})
        print(message(
            language,
            f"تم تغيير لغة الإضافة إلى {LANGUAGES[language]}",
            f"Plugin language changed to {LANGUAGES[language]}",
            f"Langue du plugin définie sur {LANGUAGES[language]}",
        ))
        return

    if action in {"help", "مساعدة", "aide"}:
        print(message(
            language,
            "استخدم: translate | translate set ar|en|fr | translate aliases",
            "Use: translate | translate set ar|en|fr | translate aliases",
            "Utilisez : translate | translate set ar|en|fr | translate aliases",
        ))
        return

    if action in {"aliases", "أوامر", "alias"}:
        print(message(language, "الأوامر المترجمة:", "Translated commands:", "Commandes traduites :"))
        for alias, command in sorted(ALIASES.items()):
            print(f"  {alias} -> {command}")
        return

    print(message(language, "أمر ترجمة غير معروف", "Unknown translation command", "Commande de traduction inconnue"))


def register(register_command):
    register_command("translate", translate, "Manage Arabic, English, and French command aliases")


def register_aliases(register_alias):
    for alias, command in ALIASES.items():
        register_alias(alias, command)
