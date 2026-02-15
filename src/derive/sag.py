def compute_sag(df):
    baseline = df["voltage"].max()
    df["vbat_sag"] = baseline - df["voltage"]
    return df
