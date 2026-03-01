import pandas as pd

# Load csv
df = pd.read_csv("books_metadata.csv")

# Keep only rows where media_type == "Text"
df = df[df["media_type"] == "Text"].copy()

# ISO-639-1 language mapping
LANG_MAP = {
    "en": "English",
    "fr": "French",
    "de": "German",
    "fi": "Finnish",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "la": "Latin",
    "el": "Greek (Modern)",
    "grc": "Greek (Ancient)",
    "ru": "Russian",
    "zh": "Chinese",
    "ja": "Japanese",
    "pl": "Polish",
    "cs": "Czech",
    "hu": "Hungarian",
    "ro": "Romanian",
    "bg": "Bulgarian",
    "sr": "Serbian",
    "hr": "Croatian",
    "sk": "Slovak",
    "sl": "Slovenian",
    "et": "Estonian",
    "lv": "Latvian",
    "lt": "Lithuanian",
    "is": "Icelandic",
    "ga": "Irish",
    "cy": "Welsh",
    "eo": "Esperanto",
    "af": "Afrikaans",
    "sw": "Swahili",
    "ar": "Arabic",
    "he": "Hebrew",
    "fa": "Persian",
    "hi": "Hindi",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "ur": "Urdu",
    "tr": "Turkish",
    "id": "Indonesian",
    "ms": "Malay",
    "vi": "Vietnamese",
    "ko": "Korean",
    "th": "Thai",
    "uk": "Ukrainian",
    "mk": "Macedonian",
    "ku": "Kurdish",
    "yi": "Yiddish",
    "sa": "Sanskrit",
    "bo": "Tibetan",
    "km": "Khmer",
    "my": "Burmese",
    "ne": "Nepali",
    "si": "Sinhala",
    "am": "Amharic",
    "zu": "Zulu",
    "xh": "Xhosa",
    "st": "Southern Sotho",
    "tn": "Tswana",
    "ts": "Tsonga",
    "ve": "Venda",
    "ss": "Swati",
    "rw": "Kinyarwanda",
    "rn": "Kirundi",
    "ha": "Hausa",
    "yo": "Yoruba",
    "ig": "Igbo",
    "mt": "Maltese",
    "bs": "Bosnian",
    "kk": "Kazakh",
    "ky": "Kyrgyz",
    "mn": "Mongolian",
    "uz": "Uzbek",
    "tk": "Turkmen",
    "az": "Azerbaijani",
    "hy": "Armenian",
    "ka": "Georgian",
    "sq": "Albanian",
    "br": "Breton",
    "oc": "Occitan",
    "rm": "Romansh",
    "gd": "Scottish Gaelic",
    "mi": "Maori",
    "sm": "Samoan",
    "fj": "Fijian",
    "to": "Tongan",
    "ht": "Haitian Creole",
    "qu": "Quechua",
    "ay": "Aymara",
    "gn": "Guarani",
    "tt": "Tatar",
    "ba": "Bashkir",
    "cv": "Chuvash",
    "os": "Ossetian",
    "ps": "Pashto",
    "dv": "Divehi",
    "tg": "Tajik",
    "lb": "Luxembourgish",
    "wa": "Walloon",
    "fo": "Faroese",
    "gl": "Galician",
    "eu": "Basque",
    "ca": "Catalan",
    "kk": "Kazakh",
    "be": "Belarusian",
    "kk": "Kazakh",
    "mg": "Malagasy",
    "so": "Somali",
    "ti": "Tigrinya",
    "ug": "Uyghur",
    "wo": "Wolof",
    "ln": "Lingala",
    "kg": "Kongo",
    "kj": "Kuanyama",
    "nr": "South Ndebele",
    "nd": "North Ndebele",
    "ny": "Chichewa",
    "lg": "Ganda",
    "ak": "Akan",
    "ee": "Ewe",
    "ff": "Fula",
    "bm": "Bambara",
    "sg": "Sango",
    "dz": "Dzongkha",
    "jv": "Javanese",
    "su": "Sundanese",
    "pa": "Punjabi",
    "gu": "Gujarati",
    "kn": "Kannada",
    "or": "Odia",
    "as": "Assamese",
    "lo": "Lao",
    "mn": "Mongolian",
    "tg": "Tajik",
    "ky": "Kyrgyz",
    "kk": "Kazakh",
    "uz": "Uzbek",
    "tk": "Turkmen",
    "ale": "Aleut",
    "ang": "Old English",
    "arp": "Arapaho",
    "bgs": "Tagabawa (Manobo)",
    "brx": "Bodo",
    "ceb": "Cebuano",
    "csb": "Kashubian",
    "enm": "Middle English",
    "fy": "Western Frisian",
    "gla": "Scottish Gaelic",
    "hai": "Haida",
    "kha": "Khasi",
    "kld": "Gamilaraay (Kamilaroi)",
    "myn": "Mayan Languages (unspecified)",
    "nah": "Nahuatl",
    "nai": "North American Indigenous Languages (unspecified)",
    "nav": "Navajo",
    "tl": "Tagalog",
    "fur": "Friulian",
    "ia": "Interlingua",
    "ilo": "Ilocano",
    "iu": "Inuktitut",
    "nap": "Neapolitan",
    "oji": "Ojibwe",
    "sco": "Scots",
    "rmq": "Caló (Iberian Romani)"
}

def convert_languages(lang_string):
    if pd.isna(lang_string):
        return []
    abbreviations = [x.strip() for x in lang_string.split(";")]
    return [LANG_MAP.get(abbrev, abbrev) for abbrev in abbreviations]

df["languages"] = df["languages"].apply(convert_languages)

# Process bookshelves --> list of clean category names
def clean_bookshelves(shelf_string):
    if pd.isna(shelf_string):
        return []
    items = [x.strip() for x in shelf_string.split(";")]
    cleaned = []
    for item in items:
        # Remove "Category:" prefix if present
        if item.lower().startswith("category:"):
            cleaned.append(item.split(":", 1)[1].strip())
        else:
            cleaned.append(item)
    return cleaned

df["bookshelves"] = df["bookshelves"].apply(clean_bookshelves)

# Process subjects --> list of clean subjects names
def clean_subjects(subject_string):
    if pd.isna(subject_string):
        return []
    items = [x.strip() for x in subject_string.split(" -- ")]
    cleaned = []

    return items

df["subjects"] = df["subjects"].apply(clean_subjects)

# Save processed csv
df.to_csv("processed_books.csv", index=False)

print("Processing complete!")