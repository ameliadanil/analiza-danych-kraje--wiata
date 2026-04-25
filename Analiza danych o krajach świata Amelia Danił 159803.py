import requests
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt

# API -> DataFrame
url = "https://restcountries.com/v3.1/all?fields=name,capital,region,subregion,population,area,currencies"

response = requests.get(url)

if response.status_code != 200:
    print("API zwróciło błąd:", response.status_code)
    print(response.text)
    raise Exception("Nie udało się pobrać danych z API")

data = response.json()


def get_capital(country):
    capital = country.get("capital")
    if capital and len(capital) > 0:
        return capital[0]
    return None


def get_currency(currencies_dict):
    if currencies_dict:
        return list(currencies_dict.keys())[0]
    return None


countries_list = []

for country in data:
    countries_list.append({
        "nazwa": country.get("name", {}).get("common"),
        "stolica": get_capital(country),
        "region": country.get("region"),
        "subregion": country.get("subregion"),
        "populacja": country.get("population"),
        "powierzchnia": country.get("area"),
        "waluta": get_currency(country.get("currencies"))
    })

kraje = pd.DataFrame(countries_list)

kraje = kraje.dropna(subset=["nazwa"])

kraje["populacja"] = pd.to_numeric(kraje["populacja"], errors="coerce")
kraje["powierzchnia"] = pd.to_numeric(kraje["powierzchnia"], errors="coerce")

print("HEAD:")
print(kraje.head())

print("\nSHAPE:")
print(kraje.shape)

print("\nDTYPES:")
print(kraje.dtypes)

print("\nBraki danych:")
print(kraje.isna().sum())


# Zapis do SQLite
conn = sqlite3.connect("kraje_swiata.db")

kraje.to_sql("kraje", conn, if_exists="replace", index=False)

print("\nDane zapisano do bazy SQLite: kraje_swiata.db")


# Analiza SQL

q1 = """
SELECT SUM(populacja) AS populacja_swiata
FROM kraje;
"""
print("\n1. Łączna populacja świata:")
print(pd.read_sql_query(q1, conn))


q2 = """
SELECT nazwa, region, populacja
FROM kraje
ORDER BY populacja DESC
LIMIT 10;
"""
print("\n2. 10 krajów z największą populacją:")
print(pd.read_sql_query(q2, conn))


q3 = """
SELECT 
    region,
    COUNT(*) AS liczba_krajow,
    ROUND(AVG(populacja), 0) AS srednia_populacja
FROM kraje
GROUP BY region
ORDER BY liczba_krajow DESC;
"""
print("\n3. Liczba krajów i średnia populacja w regionach:")
print(pd.read_sql_query(q3, conn))


q4 = """
SELECT nazwa, region, powierzchnia
FROM kraje
WHERE powierzchnia > 312679
ORDER BY powierzchnia DESC;
"""
print("\n4. Kraje większe niż Polska:")
print(pd.read_sql_query(q4, conn))


q5 = """
SELECT 
    nazwa,
    region,
    populacja,
    powierzchnia,
    ROUND(populacja / powierzchnia, 2) AS gestosc_zaludnienia
FROM kraje
WHERE powierzchnia > 0 
  AND populacja IS NOT NULL
ORDER BY gestosc_zaludnienia DESC
LIMIT 1;
"""
print("\n5. Kraj z największą gęstością zaludnienia:")
print(pd.read_sql_query(q5, conn))


q6 = """
SELECT nazwa, region, powierzchnia
FROM kraje
ORDER BY powierzchnia DESC
LIMIT 10;
"""
print("\nDodatkowo: 10 największych krajów powierzchniowo:")
print(pd.read_sql_query(q6, conn))


# Wizualizacja
q_plot = """
SELECT 
    region,
    SUM(populacja) AS populacja_regionu
FROM kraje
WHERE region IS NOT NULL
GROUP BY region
ORDER BY populacja_regionu DESC;
"""

df_plot = pd.read_sql_query(q_plot, conn)

plt.figure(figsize=(10, 6))
plt.bar(df_plot["region"], df_plot["populacja_regionu"])
plt.title("Łączna populacja według regionów świata")
plt.xlabel("Region")
plt.ylabel("Populacja")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("populacja_regionow.png", dpi=300)
plt.show()

conn.close()

print("\nWykres zapisano jako: populacja_regionow.png")
print("Zakończono analizę.")