import pandas as pd
from pathlib import Path

PROJECT_DIR = Path("/Users/hamzashah/data-platform-engineering-snowflake")

input_path = PROJECT_DIR / "datasets" / "raw" / "transaction_data.csv"
cleaned_path = PROJECT_DIR / "datasets" / "cleaned" / "cleaned_transactions.csv"

#making a function to convert the csv into a standarised format each time: UTF8
def load_csv(input_path):
    encodings = ["utf-8-sig", "utf-8", "cp1252"]

    for encoding in encodings:
        try:
            df = pd.read_csv(input_path, encoding=encoding)

            print(f"Successfully loaded CSV using: {encoding}")
            return df

        except UnicodeDecodeError:
            continue

    raise ValueError("Could not decode CSV with supported encodings")

# Load the raw CSV into a DataFrame
df = load_csv(input_path)

# stripping whitespace from the columns
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)


# 2 - removing leading and trailing whitespace in text columnns
text_cols = ["itemdescription", "country"]

for col in text_cols:
    df[col] = df[col].str.strip()


# removing duplicates from the df

original_cols = [
    "userid",
    "transactionid",
    "transactiontime",
    "itemcode",
    "itemdescription",
    "numberofitemspurchased",
    "costperitem",
    "country"
]

# convert timestamp into a datetime type
df["transactiontime"] = pd.to_datetime(
    df["transactiontime"],
    format = "%a %b %d %H:%M:%S IST %Y",
    errors="coerce"
)

#how many tiomestamps were invalid
invalid_timestamps = df["transactiontime"].isna().sum()
print("Invalid timestamps:", invalid_timestamps)

if invalid_timestamps > 0:
    print("Warning: Investigate invalid timestamps before proceeding.")

df = df.drop_duplicates(subset=original_cols).copy()

#split timestamp into date and time
df["transaction_date"] = df["transactiontime"].dt.date

df["transaction_clock_time"] = (
    df["transactiontime"].dt.time
)

# 3 - for items without a description, we can look up the same item and use that desription to fill it in
lookup = df.dropna(subset=["itemdescription"]).drop_duplicates("itemcode").set_index("itemcode")["itemdescription"]

descriptions = df["itemcode"].map(lookup)

df["itemdescription"] = df["itemdescription"].fillna(descriptions)

print(
    "Missing descriptions remaining:",
    df["itemdescription"].isna().sum()
)

#number of rows before we remove any
rows_before_filter = len(df)

# Remove rows with invalid user ID, transaction IDs, or quanitity
df = df[
    (~df["userid"].isin([-1, 0])) &
    (~df["transactionid"].isin([-1, 0])) &
    (~df["itemcode"].isin([-1, 0])) &
    (df["costperitem"] >= 0) &
    (df["numberofitemspurchased"] >= 0)
].copy()

#number of rows removed
print("Rows removed by validation rules:", rows_before_filter - len(df))


# save cleaned CSV to cleaned folder
cleaned_path.parent.mkdir(parents=True, exist_ok=True)

df.to_csv(cleaned_path, index=False, encoding="utf-8")

print("\nCleaning complete")
print(f"Saved to: {cleaned_path}")
print(f"Rows remaining: {len(df):,}")
print(f"Columns: {len(df.columns)}")
print(f"Duplicate rows remaining: {df.duplicated().sum()}")
print("\nMissing values:")
print(df.isna().sum())