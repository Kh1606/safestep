from dbfread import DBF
import pandas as pd

dbf_path = "RDL_ETCT_AS.dbf"
table = DBF(dbf_path, load=True, char_decode_errors="ignore")
df = pd.DataFrame(iter(table))

print(df.shape)
print(df.columns)
print(df.head())

df.to_csv("RDL_ETCT_AS_attributes.csv", index=False, encoding="utf-8-sig")
