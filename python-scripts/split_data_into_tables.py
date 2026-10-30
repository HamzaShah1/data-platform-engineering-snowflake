import pandas as pd
import numpy as np
from scipy.stats import zscore
from statsmodels.stats.stattools import medcouple
from pathlib import Path

PROJECT_DIR = Path("/Users/hamzashah/data-platform-engineering-snowflake")

input_path = PROJECT_DIR / "datasets" / "cleaned" / "cleaned_transactions.csv"
output_dir = PROJECT_DIR / "datasets" / "processed"

# Load the cleaned dataset
df = pd.read_csv(input_path)



# Creating outliers tables:
# only look at columns which are numeric
numeric_cols = df.select_dtypes(include="number").columns.difference(
    ["userid", "transactionid", "transactiontime", "itemcode"])

def count_adjusted_boxplot_outliers(series):
    values = series.dropna().to_numpy(dtype=float)

    q1 = np.quantile(values, 0.25)
    q3 = np.quantile(values, 0.75)
    iqr = q3-q1

    mc = medcouple(values, use_fast = True)

    # Adjust fences according to skewness
    if mc >= 0:
        lower = q1 - 1.5 * np.exp(-4 * mc) * iqr
        upper = q3 + 1.5 * np.exp(3 * mc) * iqr
    else:
        lower = q1 - 1.5 * np.exp(-3 * mc) * iqr
        upper = q3 + 1.5 * np.exp(4 * mc) * iqr

    return ((values < lower) | (values > upper)).sum()

# check for statistical outliers using medcouples
outliers_df = pd.DataFrame({
    "Column": numeric_cols,
    "Outliers": [
        count_adjusted_boxplot_outliers(df[col])
        for col in numeric_cols
    ],
    # display skew
    "Skew": [
        df[col].skew()
    for col in numeric_cols
    ],
    "Medcouple": [
        medcouple(df[col].dropna().to_numpy(dtype=float), use_fast=True)
        for col in numeric_cols
    ]
})


#create mask to filter dataframe
def adjusted_boxplot_outlier_mask(series):
    values = series.to_numpy(dtype=float)
    valid = ~np.isnan(values)
    clean_values = values[valid]

    q1 = np.quantile(clean_values, 0.25)
    q3 = np.quantile(clean_values, 0.75)
    iqr = q3 - q1

    mc = medcouple(clean_values, use_fast=True)

    if mc >= 0:
        lower = q1 - 1.5 * np.exp(-4 * mc) * iqr
        upper = q3 + 1.5 * np.exp(3 * mc) * iqr
    else:
        lower = q1 - 1.5 * np.exp(-3 * mc) * iqr
        upper = q3 + 1.5 * np.exp(4 * mc) * iqr

    mask = pd.Series(False, index=series.index)
    mask.loc[valid] = (
        (clean_values < lower) | (clean_values > upper)
    )

    return mask, lower, upper


# save the outliers into a csv
output_dir.mkdir(parents=True, exist_ok=True)

# Identify outliers independently
price_mask, price_lower, price_upper = (
    adjusted_boxplot_outlier_mask(df["costperitem"])
)

quantity_mask, quantity_lower, quantity_upper = (
    adjusted_boxplot_outlier_mask(df["numberofitemspurchased"])
)

# Keep complete transaction rows
outliers_price = df.loc[price_mask].copy()
outliers_quantity = df.loc[quantity_mask].copy()

# Export
outliers_price.to_csv(
    output_dir / "outliers_price.csv", index=False
)
outliers_quantity.to_csv(
    output_dir / "outliers_quantity.csv", index=False
)



# creating orders table:
order_columns = [
    "transactionid",
    "userid",
    "itemcode",
    "transactiontime",
    "transaction_date",
    "transaction_clock_time",
    "numberofitemspurchased",
    "costperitem",
]

orders = df[order_columns].copy()

orders.to_csv(
    output_dir / "orders.csv",
    index = False
)



# creating products table:
product_columns = [
    "itemcode",
    "itemdescription"
]

products = (df[product_columns].drop_duplicates(subset=["itemcode"]).reset_index(drop=True))

products.to_csv(
    output_dir / "products.csv",
    index = False
)



# creating customers table:
customers_columns = [
    "userid",
    "country"
]

customers = (df[customers_columns].drop_duplicates(subset=["userid"]).reset_index(drop=True))

customers.to_csv(
    output_dir / "customers.csv",
    index = False
)

# commit message4