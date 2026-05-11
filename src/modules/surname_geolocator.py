"""
surname_geolocator.py
─────────────────────
Infiere el país de origen probable de un autor a partir de su apellido,
usando reglas lingüísticas y un diccionario directo de apellidos conocidos.

Estrategia en cascada:
  1. Diccionario exacto de apellidos del dataset (máxima precisión)
  2. Patrones de sufijos / prefijos / caracteres por región lingüística
  3. País por defecto: "United States" (STEM publishing bias)
"""

from __future__ import annotations
import re
import unicodedata

# ─────────────────────────────────────────────────────────────────────────────
# 1. DICCIONARIO EXACTO
#    Apellidos que aparecen en el dataset, mapeados manualmente a su país más
#    probable basándose en origen lingüístico / étnico del apellido.
# ─────────────────────────────────────────────────────────────────────────────
EXACT_MAP: dict[str, str] = {
    # Búlgaro
    "Hadzhikoleva": "Bulgaria",
    "Hadzhikolev":  "Bulgaria",

    # Árabe / Medio Oriente
    "Siraj":    "Saudi Arabia",
    "Aidarus":  "Somalia",
    "Ahmed":    "Egypt",
    "Mohamed":  "Egypt",
    "Alsulami": "Saudi Arabia",
    "Azhar":    "Pakistan",
    "Jahan":    "Bangladesh",
    "Begum":    "Bangladesh",
    "CHIHA":    "Algeria",

    # Indio / Sur de Asia
    "Anugula":           "India",
    "Parthiban":         "India",
    "Shetty":            "India",
    "Indugu":            "India",
    "Chakraborty":       "India",
    "Karanjai":          "India",
    "Kumar":             "India",
    "Bansal":            "India",
    "Arora":             "India",
    "Tiwari":            "India",
    "Thirunavukarasu":   "India",
    "P":                 "India",
    "S":                 "India",

    # Chino / Asia Oriental
    "Mo":        "China",
    "Zhong":     "China",
    "Ran":       "China",
    "Tang":      "China",
    "Bai":       "China",
    "Cao":       "China",
    "Chen":      "China",
    "Dongshuo":  "China",
    "Fan":       "China",
    "Guo":       "China",
    "Huang":     "China",
    "Jia":       "China",
    "Li":        "China",
    "Tian":      "China",
    "Wei":       "China",
    "Wu":        "China",
    "Xuan":      "Vietnam",
    "Zhang":     "China",
    "Zhao":      "China",
    "周":        "China",
    "姜梓涵":    "China",
    "翼":        "China",
    "郭光玉":    "China",

    # Coreano
    "Jung": "South Korea",

    # Malayo / Sudeste asiático
    "Ng":      "Malaysia",
    "Chan":    "Malaysia",
    "Loo":     "Malaysia",
    "Wijanto": "Indonesia",
    "Truong":  "Vietnam",
    "Settewong": "Thailand",

    # Serbio / Balcánico
    "Petrovic": "Serbia",
    "Petkovic": "Serbia",
    "Sanda":    "Romania",

    # Ruso / Europa del Este
    "Artyukhov":     "Russia",
    "Przybyszewski": "Poland",
    "Ungureanu":     "Romania",
    "Pătruț":        "Romania",

    # Turco
    "Sinav":           "Turkey",
    "Kurt":            "Turkey",
    "POLAT":           "Turkey",
    "Karaoglan Yilmaz": "Turkey",

    # Africano / Subsahariano
    "Nana":  "Ghana",

    # Latinoamericano
    "Aguilar-Lopez":    "Mexico",
    "Albán Cuestas":    "Colombia",
    "Arista":           "Peru",
    "Balart":           "Cuba",
    "Beltre":           "Dominican Republic",
    "Contreras-Medina": "Mexico",
    "Cornide-Reyes":    "Chile",
    "Flores Portillo":  "Mexico",
    "González-Bravo":   "Mexico",
    "Kadel":            "Nepal",
    "Ricoy":            "Mexico",
    "Valdivia":         "Chile",
    "XAVIER MUNIZ":     "Brazil",

    # Italiano
    "Di Lodovico": "Italy",
    "Ferrara":     "Italy",
    "Melonis":     "Italy",

    # Portugués / Brasileño
    "Gomes": "Portugal",

    # Alemán / Austria / Suiza
    "Fleischmann": "Germany",
    "Schöning":    "Germany",
    "Offerman":    "Netherlands",

    # Inglés / Anglosajón
    "Bailey":            "United Kingdom",
    "Burbage":           "United Kingdom",
    "Chapman":           "United Kingdom",
    "Hider":             "United Kingdom",
    "Meakin":            "United Kingdom",
    "Smith-McCallister": "United States",
    "Steel":             "United Kingdom",

    # Árabe con caracteres unicode
    "إيمان": "Egypt",
    "حسن":   "Egypt",
    "علي":   "Egypt",
}

# ─────────────────────────────────────────────────────────────────────────────
# 2. REGLAS DE PATRONES LINGÜÍSTICOS
#    Se aplican en orden; la primera que coincide gana.
# ─────────────────────────────────────────────────────────────────────────────
PATTERN_RULES: list[tuple[re.Pattern, str]] = [
    # Caracteres árabes
    (re.compile(r'[\u0600-\u06FF]'),          "Egypt"),
    # Caracteres chinos / japoneses / coreanos
    (re.compile(r'[\u4E00-\u9FFF\u3040-\u30FF\uAC00-\uD7AF]'), "China"),

    # Sufijos eslavos / búlgaros / serbios
    (re.compile(r'(ov|ova|ev|eva|ic|ić|ski|ska|czyk|enko|yk)$', re.I), "Russia"),
    # Sufijos turcos
    (re.compile(r'(oğlu|oglu|yılmaz|yilmaz|çelik|celik|kaya|demir|şahin|sahin)$', re.I), "Turkey"),
    # Sufijos indios del sur
    (re.compile(r'(swamy|swami|krishna|rajan|kumar|nair|rao|reddy|iyer|naidu|patel|sharma|gupta|singh|jain|mehta|malhotra|bose|ghosh|das|dutta|mukherjee|chatterjee|banerjee|roy|sen|paul|bhat|kaur|soni|verma|mishra|pandey|trivedi|joshi|dubey|aggarwal|agarwal|kapoor|saxena|srivastava|shukla|bajpai|yadav|tiwari|chaturvedi)$', re.I), "India"),
    # Prefijos o morfemas chinos transliterados comunes
    (re.compile(r'^(wang|liu|zhang|chen|yang|huang|zhao|wu|zhou|xu|sun|ma|zhu|hu|lin|guo|he|luo|gao|zheng|tang|liang|xie|yao|wei|han|xu|feng|deng|cao|peng|zeng|xiao|tian|ding|shao|fang|shi|yan|dong|fan|cheng|bai|jia|ren|mao|qian|zou|wu|shen|lu|liao|jiang|lei|dai|yin|mo|fu|pang|xue|xiong|ou)$', re.I), "China"),
    # Nombres vietnamitas comunes
    (re.compile(r'^(nguyen|tran|le|pham|hoang|phan|vu|dang|bui|do|ho|ngo|duong|ly|truong|dinh|ta|luong|mai|luu|dao|trinh|phu|huynh)$', re.I), "Vietnam"),
    # Nombres coreanos comunes
    (re.compile(r'^(kim|lee|park|choi|jung|kang|cho|yoon|jang|lim|han|oh|shin|kwon|hong|seo|yang|ko|moon|son|chun|bae|ahn|ryu|jeon|ha|kwak|cha|nam|yoo|joo|chun|baek)$', re.I), "South Korea"),
    # Japonés transliterado
    (re.compile(r'^(tanaka|suzuki|sato|watanabe|ito|yamamoto|nakamura|kobayashi|kato|yoshida|yamada|sasaki|yamaguchi|matsumoto|inoue|kimura|hayashi|shimizu|yamazaki|mori|ikeda|hashimoto|yamashita|ishikawa|nakajima|fujita|ogawa|goto|ota|hasegawa|maeda|fujii|nishimura|murakami)$', re.I), "Japan"),
    # Malayo / indonesio
    (re.compile(r'(bin|binti|ahmad|mohd|abd|abdul|ismail|hassan|ibrahim|rahman|rahim|razak|aziz|osman|omar|ali|hamid|kadir|jamal|latif|amin)$', re.I), "Malaysia"),
    # Tailandés
    (re.compile(r'(wong|wong|suporn|siri|chai|porn|rat|nok|sri|suk|nut|pong|nat|yada)$', re.I), "Thailand"),
    # Latino hispano
    (re.compile(r'(ez|oz|az|iz|ez|ón|os|as)([-\s]|$)', re.I), "Mexico"),
    (re.compile(r'(andez|andez|uez|iez|aez)([-\s]|$)', re.I), "Spain"),
    # Portugués / Brasileño
    (re.compile(r'(eira|eiro|inho|inha|ões|ção|são|ão)$', re.I), "Brazil"),
    # Italiano
    (re.compile(r'(elli|etti|ini|oni|ino|ino|elli|ati|ati|ari|ori|eri|ieri|ucci|acci|icci)([-\s]|$)', re.I), "Italy"),
    # Alemán
    (re.compile(r'(mann|berg|burg|stein|feld|bach|haus|dorf|hagen|brandt|schmidt|schneider|müller|muller|bauer|schäfer|schaefer|hoffmann|krause|richter|klein|wolf|lange|lehmann|neumann|schulz|maier|meyer|becker|fischer|braun|herrmann|koehler|hartmann|zimmermann|kramer|kruger|vogel|roth|mayer|hahn|kaiser|weiss|otto|schwarze)([-\s]|$)', re.I), "Germany"),
    # Ruso / ucraniano
    (re.compile(r'(ov|ova|ev|eva|enko|chuk|sky|ski|ska|chy|ich)([-\s]|$)', re.I), "Russia"),
    # Polaco
    (re.compile(r'(ski|ska|cki|cka|wski|wska|czyk|iak|ak|ek|nik)([-\s]|$)', re.I), "Poland"),
    # Rumano
    (re.compile(r'(escu|eanu|anu|aru|aru|iu|ean|ean)([-\s]|$)', re.I), "Romania"),
    # Griego
    (re.compile(r'(opoulos|oulos|akis|idis|ides|aris|aris|as|is)([-\s]|$)', re.I), "Greece"),
    # Francés
    (re.compile(r'(eau|ault|ois|ois|ard|ier|ier|el|et)([-\s]|$)', re.I), "France"),
    # Nórdico / Escandinavo
    (re.compile(r'(sen|ssen|son|sson|berg|dahl|dal|vik|land|lund|strom|ström|bjorn|bjørn)([-\s]|$)', re.I), "Sweden"),
    # Africano subsahariano (patrones nigerianos, ghaneses, etc.)
    (re.compile(r'(obi|nna|eze|chi|ike|ade|ola|wale|emeka|chukwu|uche|nkem|tunde|babatunde|akin|bello|ibrahim|musa|lawal|yusuf|abdullahi|aliyu|usman|adamu|sani)([-\s]|$)', re.I), "Nigeria"),
]

# ─────────────────────────────────────────────────────────────────────────────
# 3. FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────
def _normalize(s: str) -> str:
    """Normaliza el apellido: sin acentos, lowercase, sin espacios extra."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c)).lower().strip()


def infer_country(surname: str) -> str:
    """
    Devuelve el país de origen probable dado un apellido.
    Cascade: exact_map → pattern_rules → default.
    """
    if not surname or not isinstance(surname, str):
        return "Unknown"

    surname = surname.strip()

    # 1. Coincidencia exacta (case-insensitive, ignorando acentos)
    key_norm = _normalize(surname)
    for k, country in EXACT_MAP.items():
        if _normalize(k) == key_norm:
            return country

    # 2. Patrones lingüísticos
    for pattern, country in PATTERN_RULES:
        if pattern.search(surname):
            return country

    # 3. Default
    return "United States"


def extract_first_surname(authors_str: str) -> str:
    """
    Dado el campo 'authors' (ej. 'Smith, John; Doe, Jane'),
    extrae el apellido del primer autor.
    """
    if not authors_str or not isinstance(authors_str, str):
        return ""
    first_author = authors_str.split(";")[0].strip()
    if "," in first_author:
        return first_author.split(",")[0].strip()
    parts = first_author.split()
    return parts[0].strip() if parts else ""


def get_country_from_authors(authors_str: str) -> str:
    """Wrapper conveniente: autores → país."""
    surname = extract_first_surname(authors_str)
    return infer_country(surname) if surname else "Unknown"
