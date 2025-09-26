import csv
import random
import os
import string
from faker import Faker
from faker.providers import BaseProvider
from tqdm import tqdm

# ---------- Categorías de vehículos ----------
CATEGORIAS = [
    "urbanos","sedán","berlina","cupé","descapotable",
    "deportivo","todoterreno","monovolumen","SUV"
]

# ---------- Abreviaturas de provincias (formato antiguo hasta 1999) ----------
PROVINCIAS = [
    "A","AB","AL","AV","B","BA","BI","BU","C","CA","CC","CE","CO","CR","CS","CU",
    "GC","GI","GR","GU","H","HU","J","L","LE","LO","LU","M","MA","ML","MU","NA",
    "O","OR","P","PM","PO","S","SA","SE","SG","SO","SS","T","TE","TF","TO","V",
    "VA","VI","Z","ZA"
]

SERIES_MATRICULAS = {
    2000: ["BBJ","BCD","BCY","BDR"],
    2001: ["BFJ","BGF","BHG","BJC","BKB","BLC","BMF","BMW","BNL","BPG","BRB","BRT"],
    2002: ["BSL","BTF","BTZ","BVW","BWT","BXP","BYP","BZF","BZV","CBP","CCH","CDC"],
    2003: ["CDV","CFM","CGJ","CHF","CJC","CKB","CLD","CLV","CMM","CNK","CPF","CRC"],
    2004: ["CRV","CSS","CTT","CVR","CWR","CXT","CYY","CZP","DBJ","DCH","DDG","DFF"],
    2005: ["DFZ","DGX","DHZ","DKB","DLD","DMJ","DNP","DPK","DRG","DSC","DTB","DVB"],
    2006: ["DVW","DWT","DXZ","DYY","FBC","FCJ","FDP","FFK","FGF","FHD","FJD","FKC"],
    2007: ["FKY","FLV","FNB","FNZ","FRC","FSJ","FTP","FVJ","FWC","FXB","FXY","FYY"],
    2008: ["FZR","GBN","GCK","GDH","GFC","GFY","GGV","GHG","GHT","GJJ","GJV","GKH"],
    2009: ["GKS","GLC","GLP","GMC","GMN","GNF","GNY","GPJ","GPW","GRM","GSC","GSR"],
    2010: ["GTC","GTS","GVM","GWC","GWV","GXP","GYD","GYM","GYX","GZJ","GZT","HBG"],
    2011: ["HBP","HCB","HCR","HDC","HDR","HFF","HFT","HGC","HGM","HGX","HHH","HHT"],
    2012: ["HJC","HJM","HKB","HKL","HKX","HLK","HLW","HMD","HML","HMT","HNC","HNK"],
    2013: ["HNT","HPC","HPN","HPY","HRK","HRX","HSK","HSR","HSZ","HTK","HTV","HVF"],
    2014: ["HVN","HVZ","HWM","HWY","HXN","HYD","HYT","HZB","HZL","HZZ","JBL","JBY"],
    2015: ["JCK","JCY","JDR","JFG","JFX","JGR","JHJ","JHT","JJH","JJW","JKK","JKZ"],
    2016: ["JLN","JMF","JMY","JNR","JPK","JRG","JRZ","JSL","JTB","JTR","JVH","JVZ"],
    2017: ["JWN","JXF","JYB","JYT","JZP","KBM","KCH","KCV","KDK","KFC","KFW","KGN"],
    2018: ["KHG","KHY","KJV","KKR","KLN","KMM","KNK","KPD","KPS","KRJ","KRZ","KSS"],
    2019: ["KTJ","KVB","KVX","KWT","KXR","KYN","KZK","KZY","LBN","LCG","LCY","LDR"],
    2020: ["LFH","LFY","LGG","LGH","LGP","LHG","LJD","LJR","LKF","LKV","LLJ","LMC"],
    2021: ["LML","LMX","LNN","LPD","LPW","LRP","LSG","LSR","LTD","LTP","LVD","LVV"],
    2022: ["LWD","LWR","LXD","LXS","LYJ","LYZ","LZP","LZZ","MBN","MCB","MCR","MDF"],
    2023: ["MDS","MFG","MFZ","MGN","MHG","MJB","MJR","MKD","MKR","MLH","MLY","MMN"],
    2024: ["MNC","MNT","MPL","MRD","MRX","MSS","MTK","MTW","MVL","MWD","MWV","MXP"],
    2025: ["MYF","MYW","MZS","NBL","NCJ","NDG","NFC","NFR","NGB"],
}

WMI_POR_MARCA = {
    "Volkswagen": "WVW","SEAT": "VSS","Renault": "VF1","BMW": "WBA","Audi": "WAU",
    "Mercedes-Benz": "WDB","Fiat": "ZFA","Peugeot": "VF3","Citroën": "VF7","Opel": "W0L",
    "Ford": "WF0","Toyota": "SB1","Nissan": "SJN","Hyundai": "TMA","Kia": "KNA",
    "Mazda": "JMZ","Mitsubishi": "JMB","Volvo": "YV1","Skoda": "TMB","Dacia": "UU1"
}

VIN_AÑO_CODIGO = {
    1990:"L", 1991:"M", 1992:"N", 1993:"P", 1994:"R", 1995:"S", 1996:"T", 1997:"V", 1998:"W", 1999:"X",
    2000:"Y", 2001:"1", 2002:"2", 2003:"3", 2004:"4", 2005:"5", 2006:"6", 2007:"7", 2008:"8", 2009:"9",
    2010:"A", 2011:"B", 2012:"C", 2013:"D", 2014:"E", 2015:"F", 2016:"G", 2017:"H", 2018:"J", 2019:"K",
    2020:"L", 2021:"M", 2022:"N", 2023:"P", 2024:"R", 2025:"S"
}

# ---------- Funciones ----------
def leer_ids_usuarios(fichero_usuarios: str = "users.csv") -> list[str]:
    """Lee los DNIs de los usuarios desde el fichero CSV."""
    if not os.path.exists(fichero_usuarios):
        raise FileNotFoundError("No se encontró users.csv. Ejecuta antes usuarios.py")
    ids = []
    with open(fichero_usuarios, encoding="utf-8") as f:
        lector = csv.DictReader(f)
        for fila in lector:
            if fila.get("IdNumber"):
                ids.append(fila["IdNumber"])
    return ids

def generar_vin(marca: str, año: int, usados: set) -> str:
    """
    Genera un VIN de 17 caracteres coherente con la marca y el año.
    - WMI según marca
    - VDS (pos. 4–9) aleatorio (6 chars válidos)
    - VIS (pos. 10–17): incluye código de año en la pos. 10
    """
    vin_chars = "ABCDEFGHJKLMNPRSTUVWXYZ0123456789"
    wmi = WMI_POR_MARCA.get(marca, random.choice(list(WMI_POR_MARCA.values())))
    vds = "".join(random.choice(vin_chars) for _ in range(6))
    year_code = VIN_AÑO_CODIGO.get(año, "X")
    vis_rest = "".join(random.choice(vin_chars) for _ in range(7))
    vin = wmi + vds + year_code + vis_rest
    while vin in usados:
        vds = "".join(random.choice(vin_chars) for _ in range(6))
        vis_rest = "".join(random.choice(vin_chars) for _ in range(7))
        vin = wmi + vds + year_code + vis_rest
    usados.add(vin)
    return vin


# Marcas y modelos (extraído de conjuntos_datos/modelos.csv)
def cargar_modelos_csv(ruta: str):
    historico = {}
    categorias = {}
    with open(ruta, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for fila in reader:
            marca = fila["Marca"]
            modelo = fila["Modelo"]
            inicio = int(fila["Inicio"])
            fin = int(fila["Fin"])
            cats = fila["Categorias"].split("|")
            if marca not in historico:
                historico[marca] = {}
            historico[marca][modelo] = (inicio, fin)
            categorias[modelo] = cats
    return historico, categorias

MODELOS_POR_MARCA, CATEGORIAS_POR_MODELO = cargar_modelos_csv("modelos.csv")


def generar_matricula_moderno(año: int) -> str:
      # Formato moderno: 4 números + 3 letras (sin vocales ni Ñ, Q)
    numeros = random.randint(1000, 9999)
    if año in SERIES_MATRICULAS:
        serie = random.choice(SERIES_MATRICULAS[año])
    else:
        # si el año no está en la tabla, usamos la última serie conocida
        serie = random.choice(SERIES_MATRICULAS[max(SERIES_MATRICULAS.keys())])
    return f"{numeros} {serie}"
 
def generar_matricula(año: int) -> str:
    """Genera una matrícula coherente con el año (sistema antiguo o nuevo)."""
    if año < 2000:  
        # Formato antiguo: Provincia + 4 números + 2 letras
        provincia = random.choice(PROVINCIAS)
        numeros = random.randint(1000, 9999)
        letras = ''.join(random.choices(string.ascii_uppercase, k=2))
        return f"{provincia}-{numeros}-{letras}"
    else:
        return generar_matricula_moderno(año)

def generar_vehiculos(ids_usuarios: list[str], max_por_usuario: int) -> list[dict]:
    fake = Faker("es_ES")
    vehiculos = []
    matriculas_usadas = set()
    vins_usados = set()
    for uid in tqdm(ids_usuarios, desc="Generando vehículos"):
        cantidad = random.randint(0, max_por_usuario)
        for _ in range(cantidad):
            año = fake.random_int(1990, 2025)
            # Matrícula
            matricula = generar_matricula(año)
            while matricula in matriculas_usadas:
                matricula = generar_matricula(año)
            matriculas_usadas.add(matricula)
            # Marca, modelo y categoría
            while True:
                marca = fake.random_element(list(MODELOS_POR_MARCA.keys()))
                modelo = fake.random_element(list(MODELOS_POR_MARCA[marca].keys()))
                inicio, fin = MODELOS_POR_MARCA[marca][modelo]
                if inicio <= año <= fin:
                    break
            # VIN
            vin = generar_vin(marca, año, vins_usados)
            vehiculos.append({
                "Matricula": matricula,
                "VIN": vin,
                "Año": año,
                "Fabricante": marca,
                "Modelo": modelo,
                "Categoria": fake.random_element(CATEGORIAS_POR_MODELO.get(modelo, CATEGORIAS)),
                "DNI_Propietario": uid,
            })
    return vehiculos

def write_csv(filas: list[dict], ruta: str) -> None:
    """Escribe la lista de vehículos en un CSV."""
    cabecera = ["Matricula","VIN","Año","Fabricante","Modelo","Categoria","DNI_Propietario"]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=cabecera)
        escritor.writeheader()
        escritor.writerows(filas)

# ---------- MAIN ----------
if __name__ == "__main__":
    MAX_POR_USUARIO = 3
    FICHERO_USUARIOS = "conjunto_datos/users.csv"
    FICHERO_SALIDA = "conjunto_datos/vehiculos.csv"

    ids_usuarios = leer_ids_usuarios(FICHERO_USUARIOS)
    vehiculos = generar_vehiculos(ids_usuarios, MAX_POR_USUARIO)
    write_csv(vehiculos, FICHERO_SALIDA)
    print(f"Generado {FICHERO_SALIDA}")
