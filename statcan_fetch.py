import requests
import pandas as pd

# 1. Liste des tableaux disponibles
def get_all_cubes():
    url = "https://www150.statcan.gc.ca/t1/wds/rest/getAllCubesList"
    response = requests.get(url)
    return response.json()["object"]

# 2. Liste des vecteurs dans un tableau donné
def get_cube_metadata(product_id):
    url = f"https://www150.statcan.gc.ca/t1/wds/rest/getCubeMetadata/{product_id}"
    response = requests.get(url)
    return response.json()["object"]

# 3. Récupérer les données d’un vecteur
def get_vector_data(vector_id):
    url = f"https://www150.statcan.gc.ca/t1/wds/rest/getDataFromVector/{vector_id}"
    response = requests.get(url)
    return response.json()["object"]

# Exemple d'utilisation
if __name__ == "__main__":
    cubes = get_all_cubes()
    print(f"Nombre total de tableaux disponibles : {len(cubes)}")

    # Exemple : prendre un tableau d’économie (filtrable selon mot-clé)
    sample = next((cube for cube in cubes if "Gross domestic product" in cube["cubeTitleEn"]), None)
    if sample:
        print(f"\nExemple sélectionné : {sample['cubeTitleEn']}")
        metadata = get_cube_metadata(sample["productId"])
        vector_ids = metadata["vectorIds"][:3]  # Prendre quelques indicateurs

        for vid in vector_ids:
            data = get_vector_data(vid)
            df = pd.DataFrame(data)
            print(f"\nDonnées du vecteur {vid} :")
            print(df[["REF_DATE", "VALUE", "GEO"]].head())

