import csv
import os
import random
import unicodedata
from typing import List, Dict
from faker import Faker
from faker.providers import BaseProvider
from tqdm import tqdm

# ============================ Configuración ============================

POSTAL_FILE = "codigos_postales_municipios.csv"
OUT_FILE = "conjunto_datos/users.csv"

NUM_USERS = 1000
P_MOBILE = 0.85
P_LANDLINE = 0.55
FORCE_AT_LEAST_ONE = False

# ===================== Mapa código provincia ===========================

PROV_BY_CODE = {
    "01":"Álava","02":"Albacete","03":"Alicante","04":"Almería","05":"Ávila","06":"Badajoz",
    "07":"Baleares","08":"Barcelona","09":"Burgos","10":"Cáceres","11":"Cádiz","12":"Castellón",
    "13":"Ciudad Real","14":"Córdoba","15":"La Coruña","16":"Cuenca","17":"Gerona","18":"Granada",
    "19":"Guadalajara","20":"Guipúzcoa","21":"Huelva","22":"Huesca","23":"Jaén","24":"León",
    "25":"Lérida","26":"La Rioja","27":"Lugo","28":"Madrid","29":"Málaga","30":"Murcia",
    "31":"Navarra","32":"Orense","33":"Asturias","34":"Palencia","35":"Las Palmas","36":"Pontevedra",
    "37":"Salamanca","38":"Santa Cruz de Tenerife","39":"Cantabria","40":"Segovia","41":"Sevilla",
    "42":"Soria","43":"Tarragona","44":"Teruel","45":"Toledo","46":"Valencia","47":"Valladolid",
    "48":"Vizcaya","49":"Zamora","50":"Zaragoza","51":"Ceuta","52":"Melilla"
}

# ============================ Provider DNI ============================

class DNIProvider(BaseProvider):
    __LETTERS = 'TRWAGMYFPDXBNJZSQVHLCKE'
    def dni_number(self) -> int:
        return self.generator.random_int(min=11111111, max=99999999)
    def dni_control_letter(self, num: int) -> str:
        return self.__LETTERS[num % 23]
    def dni(self) -> str:
        num = self.dni_number()
        return f"{num:08d}-{self.dni_control_letter(num)}"

# ============================ Utilidades ===============================

def _norm(s: str) -> str:
    """Normaliza cabeceras: minúsculas, sin acentos, con '_' en lugar de espacios."""
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.replace(" ", "_")

def load_postal_rows(path_csv: str) -> List[Dict]:
    """
    Lee CP y ciudad del CSV, y obtiene provincia por CIUDAD:
      - Si el CSV trae 'provincia', la usa directamente (city -> provincia).
      - Si NO trae 'provincia', intenta usar 'municipio_id' y mapea su prefijo (01..52) a provincia.
    NO se deriva provincia por CP. Si faltan ambas (provincia y municipio_id), se lanza error.
    Devuelve dicts: {'cp','city','prov'}
    """
    if not os.path.exists(path_csv):
        raise FileNotFoundError(f"No se encontró '{path_csv}'")

    rows: List[Dict] = []
    with open(path_csv, encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise RuntimeError("El CSV no tiene cabeceras.")
        fieldmap = {_norm(k): k for k in r.fieldnames}

        cp_key   = fieldmap.get("codigo_postal") or fieldmap.get("cp")
        city_key = (fieldmap.get("municipio_nombre") or fieldmap.get("municipio") or
                    fieldmap.get("localidad") or fieldmap.get("poblacion"))
        prov_key = fieldmap.get("provincia") or fieldmap.get("province")
        muni_id_key = (fieldmap.get("municipio_id") or fieldmap.get("codigo_municipio") or
                       fieldmap.get("id_municipio") or fieldmap.get("codigo_ine_municipio"))

        if not cp_key or not city_key:
            raise RuntimeError(
                f"Cabeceras encontradas: {r.fieldnames}. "
                "Necesito 'codigo_postal' y 'municipio_nombre' (o variantes)."
            )

        for row in r:
            cp = (row.get(cp_key) or "").strip()
            city = (row.get(city_key) or "").strip()
            if not (cp and city and cp.isdigit()):
                continue
            cp = cp.zfill(5)
            if len(cp) != 5:
                continue

            muni_id = (row.get(muni_id_key) or "").strip() if muni_id_key else ""
            if muni_id:
                code = str(muni_id).zfill(2)[:2]   # tomamos los 2 primeros dígitos
                prov = PROV_BY_CODE.get(code, "")

            if not prov: # control de errores de provincia: en caso de que se genere mal, no pone provincia
                continue

            rows.append({"cp": cp, "city": city, "prov": prov})

    if not rows:
        raise RuntimeError(
            "No encontré filas válidas con CP, ciudad y provincia por ciudad. "
            "Asegúrate de que el CSV incluya 'provincia' o 'municipio_id'."
        )
    return rows

def normalize_email(fake: Faker, name: str) -> str:
    base = (
        name.replace(" ", ".")
            .replace(",", "")
            .replace("'", "")
            .replace("´", "")
            .replace("`", "")
            .lower()
    )
    domain = fake.free_email_domain()
    return f"{base}@{domain}"

def random_spanish_mobile(fake: Faker) -> str:
    return random.choice(["6", "7"]) + "".join(str(fake.random_int(0, 9)) for _ in range(8))

def random_spanish_landline(fake: Faker) -> str:
    return random.choice(["8", "9"]) + "".join(str(fake.random_int(0, 9)) for _ in range(8))

# ===================== Generación de usuarios ==========================

def generate_users(n: int, postal_rows: List[Dict]) -> List[Dict]:
    fake = Faker("es_ES")
    fake.add_provider(DNIProvider)
    data: List[Dict] = []

    for _ in tqdm(range(n), desc="Generando usuarios"):
        sel = random.choice(postal_rows)
        cp, city, prov = sel["cp"], sel["city"], sel["prov"]
        name = fake.name()

        # teléfonos con probabilidad independiente (pueden faltar ambos)
        mobile = random_spanish_mobile(fake) if random.random() < P_MOBILE else ""
        landline = random_spanish_landline(fake) if random.random() < P_LANDLINE else ""
        if FORCE_AT_LEAST_ONE and not mobile and not landline:
            mobile = random_spanish_mobile(fake)

        row = {
            "Name": name,
            "IdNumber": fake.unique.dni(),
            "Email": normalize_email(fake, name),
            "MobilePhone": mobile,
            "LandlinePhone": landline,
            "Address": fake.street_address(),
            "City": city,
            "PostCode": cp,
            "Province": prov,
        }
        data.append(row)
    return data

def write_csv(rows: List[Dict], path: str) -> None:
    if not rows:
        return
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

# ================================ MAIN ================================

if __name__ == "__main__":
    postal_rows = load_postal_rows(POSTAL_FILE)
    users = generate_users(NUM_USERS, postal_rows)
    write_csv(users, OUT_FILE)
    print(f"Generado {OUT_FILE} con {len(users)} usuarios.")