import pandas as pd
import bar_chart_race as bcr

# Load dataset
df = pd.read_csv("popes.csv")

# Take top 10 oldest popes
top_popes = df.sort_values("age_end", ascending=False).head(10)
names = top_popes["name_full"].tolist()

# Create DataFrame for bar chart race
records = []

for i in range(len(names)):
    # At frame i, show the ages of the top i+1 popes
    snapshot = pd.Series(
        [top_popes.loc[top_popes.index[j], "age_end"] for j in range(i + 1)],
        index=names[: i + 1],
    )
    records.append(snapshot)

race_df = pd.DataFrame(records).fillna(0)

bcr.bar_chart_race(
    df=race_df,
    filename="oldest_popes_final_ages.mp4",
    orientation="h",
    sort="desc",
    n_bars=10,
    fixed_order=False,
    fixed_max=True,
    steps_per_period=20,
    interpolate_period=False,
    period_length=200,
    title="Top 10 Oldest Popes in History",
    bar_size=0.95,
)
