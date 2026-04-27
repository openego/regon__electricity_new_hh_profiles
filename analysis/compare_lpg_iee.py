import pandas as pd

path_parquet = "/home/sarah/Dokumente/new_hh_profiles/lpg/hh_el_load_profiles_lpg.parquet"
path_iee = "/home/sarah/Dokumente/new_hh_profiles/hh_el_load_profiles_100k.hdf"

df = pd.read_parquet(path_parquet)
df = df[["CHR07a00000", "CHR07a00001", "CHR07a00002"]]
print(df.head())      # first 5 rows
print(df.columns)     # column names
print(df.info())      # structure

with pd.HDFStore(path_iee, mode="r") as store:
    print(store.keys())
#df = pd.read_hdf(path_iee, key="/hh_el_load_profiles")
df = pd.read_hdf(path_iee, start=0, stop=1000)
df = df[["SOa00000", "SOa00001", "SOa00002", "SOa00003", "SOa00004", "SOa00005"]]

print(df.head())      # first 5 rows
print(df.columns)     # column names
print(df.info())      # structure