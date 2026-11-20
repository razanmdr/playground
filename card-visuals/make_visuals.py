"""Dark, on-brand card visuals (1080x400) rendered from each project's real data."""
import json, base64, io, collections
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from PIL import Image

R = Path("/home/claude/razanmdr"); OUT = Path("/home/claude/visuals/out"); OUT.mkdir(exist_ok=True)
BG, LINE, INK, MUTED = "#0B1120", "#1B2740", "#E8EEF8", "#8A97AD"
ACC, PROMPT, SIG = "#5EE0EA", "#A6E36E", "#F2B36A"
MONO = "DejaVu Sans Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 24, "axes.edgecolor": LINE, "text.color": MUTED,
                     "xtick.color": MUTED, "ytick.color": MUTED, "axes.labelcolor": MUTED})

def canvas(cmd, left=0.1):
    fig = plt.figure(figsize=(10.8, 5.2), dpi=100, facecolor=BG)
    g = fig.add_axes([0, 0, 1, 1], zorder=-1); g.set_xlim(0, 1080); g.set_ylim(0, 520); g.axis("off")
    for x in range(0, 1081, 48): g.axvline(x, color=LINE, lw=0.6, alpha=.55)
    for y in range(0, 521, 48): g.axhline(y, color=LINE, lw=0.6, alpha=.55)
    fig.text(0.035, 0.89, "$", color=PROMPT, fontsize=30, weight="bold")
    fig.text(0.07, 0.89, cmd, color=MUTED, fontsize=30)
    ax = fig.add_axes([left, 0.12, 0.95 - left, 0.66]); ax.set_facecolor("none")
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_color(LINE)
    ax.tick_params(length=0, labelsize=22)
    return fig, ax

def save(fig, name):
    fig.savefig(OUT / f"{name}.png", facecolor=BG); plt.close(fig)

# 1 Fraud monitor: weekly actual vs predicted fraud rate, reference → analysis
ml = R / "machine_learning"
f = pd.concat([pd.read_csv(ml/"Monitoring A Financial Fraud Detection Model/reference.csv"),
               pd.read_csv(ml/"Monitoring A Financial Fraud Detection Model/analysis.csv")])
f["timestamp"] = pd.to_datetime(f["timestamp"]); w = f.set_index("timestamp").resample("W")
acc = w.apply(lambda d: (d.predicted_fraud == d.is_fraud).mean() if len(d) else np.nan)
fig, ax = canvas("nannyml estimate", left=0.08)
ax.plot(acc.index, acc.values * 100, color=ACC, lw=2.6)
split = pd.Timestamp("2018-11-01"); ax.axvline(split, color=SIG, lw=1.5, ls="--")
ax.text(split, ax.get_ylim()[1], "  analysis →", color=SIG, va="top", fontsize=22)
pass; ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y")); ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=[1,7]))
save(fig, "fraud")

# 2 Service desk: most frequent content words
txt = json.load(open(ml/"Service Desk Ticket Classification with Deep Learning/text.json"))
stop = set("the . i to , and a my that of was in on they for me not this have is with it $ from { } as had be ) ( `` would an by at we '' they 's n't been but or are were so you their them xxxx xx 'm will did me all any there when what if no has do which can also get could after told about because than said one out over".split())
cnt = collections.Counter(w for t in txt for w in t if w not in stop and w.isalpha() and len(w) > 2).most_common(7)[::-1]
cnt = cnt[-5:]
fig, ax = canvas("tokenize tickets.json", left=0.22)
ax.barh([w for w, _ in cnt], [c for _, c in cnt], color=ACC, height=.55); ax.spines["left"].set_visible(False)
ax.tick_params(axis="y", labelcolor=INK); ax.set_xticks([])
save(fig, "servicedesk")

# 3 Subscriber churn: engagement scatter by status
s = pd.read_csv(ml/"Combating Subscriber Churn with Targeted Marketing/data/AZWatch_subscribers.csv")
fig, ax = canvas("predict churn", left=0.08)
for st, col in (("subscribed", ACC), ("churned", SIG)):
    d = s[s.subscription_status == st]; ax.scatter(d.engagement_time, d.engagement_frequency, s=26, color=col, alpha=.75, label=st, lw=0)

ax.legend(frameon=False, labelcolor=INK, loc="lower left", bbox_to_anchor=(0, 0.98), ncol=2, fontsize=20, handlelength=1, markerscale=2)
save(fig, "subscriber")

# 4 Clothing classifier: the notebook's Fashion-MNIST sample grid, tinted
nb = json.load(open(next((ml/"Building an E-Commerce Clothing Classifier Model with Keras").glob("notebook.ipynb"))))
png = next(o["data"]["image/png"] for c in nb["cells"] for o in c.get("outputs", []) if "image/png" in o.get("data", {}))
im = Image.open(io.BytesIO(base64.b64decode(png))).convert("L")
arr = np.asarray(im, dtype=float) / 255
# notebook figure: white bg, dark-on-white thumbnails → keep thumbnail pixels only
fig, ax = canvas("train cnn fashion")
cmap = matplotlib.colors.LinearSegmentedColormap.from_list("t", [BG, "#123044", ACC])
arr = 1 - arr if arr.mean() > .5 else arr
ys, xs = np.where(arr > .08); arr = arr[ys.min():ys.max()+1, xs.min():xs.max()+1]
arr = np.hstack([arr, np.zeros((arr.shape[0], 12)), arr, np.zeros((arr.shape[0], 12)), arr])
ax.set_position([0.04, 0.06, 0.92, 0.76]); ax.imshow(arr, cmap=cmap, aspect="equal"); ax.axis("off")
save(fig, "clothing")

de = R / "data_eng"
# 5 Retail pipeline: avg weekly sales by month
a = pd.read_csv(de/"Building a Retail Data Pipeline/agg_data.csv")
fig, ax = canvas("etl retail", left=0.08)
ax.bar(a.Month.astype(int), a.Avg_Sales / 1000, color=[SIG if v == a.Avg_Sales.max() else ACC for v in a.Avg_Sales], width=.6)
ax.set_xticks(range(1, 13), ["J","F","M","A","M","J","J","A","S","O","N","D"][:len(a)] if len(a) == 12 else a.Month.astype(int))

save(fig, "retail")

# 6 Energy ETL: avg electricity price by sector over time
e = pd.read_csv(de/"Powering Data for the Department of Energy - Building an ETL Pipeline/electricity_sales.csv")
e = e[(e.price > 0) & e.sectorName.isin(["residential", "commercial", "industrial"])]
e["period"] = pd.to_datetime(e.period); p = e.groupby(["period", "sectorName"]).price.mean().unstack()
fig, ax = canvas("etl electricity.json", left=0.08)
for col, c in zip(["residential", "commercial", "industrial"], [ACC, SIG, PROMPT]):
    if col in p: ax.plot(p.index, p[col], color=c, lw=2.4, label=col)
pass; ax.legend(frameon=False, labelcolor=INK, fontsize=20, loc="lower left", bbox_to_anchor=(0, 0.98), ncol=3, handlelength=1)
ax.set_ylim(p.min().min() - 1, p.max().max() + 1); ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y")); ax.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=[1,5,9]))
save(fig, "energy")

# 7 Orders (PySpark): orders by time of day
o = pd.read_parquet(de/"Cleaning an Orders Dataset with PySpark/orders_data_clean.parquet")
order = ["morning", "afternoon", "evening", "night"]; vc = o.time_of_day.value_counts().reindex([x for x in order if x in o.time_of_day.unique()])
fig, ax = canvas("spark-submit orders.py", left=0.08)
ax.bar(vc.index, vc.values / 1000, color=ACC, width=.5)
ax.tick_params(axis="x", labelcolor=INK)
save(fig, "orders")

# 8 Bank marketing: success rate by contact month
b = pd.read_csv(de/"Cleaning Bank Marketing Campaign Data/bank_marketing.csv")
months = ["mar","apr","may","jun","jul","aug","sep","oct","nov","dec"]
r = b.groupby("month").campaign_outcome.apply(lambda x: (x == "yes").mean() * 100).reindex([m for m in months if m in b.month.unique()])
fig, ax = canvas("dbt run campaign", left=0.08)
r.index = [m.capitalize() for m in r.index]; ax.tick_params(axis="x", labelsize=18)
ax.bar(r.index, r.values, color=[SIG if v == r.max() else ACC for v in r.values], width=.6); pass
save(fig, "bank")

# 9 London travel: journeys by type
t = pd.read_csv(de/"Exploring London's Travel Network/tfl_journeys_final.csv")
y = t.groupby(["year", "journey_type"]).journeys_millions.sum().unstack()
y = y[y.index < y.index.max()] if (t.year == t.year.max()).sum() < (t.year == t.year.min()).sum() else y
fig, ax = canvas("snowsql -f tfl.sql", left=0.13)
top = y.sum().sort_values(ascending=False).index[:3]
for col, c in zip(top, [ACC, SIG, PROMPT]): ax.plot(y.index, y[col], color=c, lw=2.4, marker="o", ms=4, label=col)
ax.legend(frameon=False, labelcolor=INK, fontsize=20, loc="lower left", bbox_to_anchor=(0, 0.98), ncol=3, handlelength=1)
save(fig, "london")
print(sorted(p.name for p in OUT.iterdir()))
