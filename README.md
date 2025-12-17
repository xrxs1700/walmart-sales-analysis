# Walmart Sales Cleaning & Analysis

This project analyzes Walmart weekly sales data to answer key business questions through a reproducible notebook workflow that cleans, explores, and visualizes trends across holidays, store economics, and macro indicators. The notebook’s insights are then transformed into an interactive Dash + Plotly dashboard to make the findings easy to explore and share.

<img width="2292" height="3092" alt="walmart-dashboard-img" src="https://github.com/user-attachments/assets/d6231779-ef3a-4064-8265-e3d0dfe30d01" />

## Dataset
- Source: [Kaggle – Walmart Sales](https://www.kaggle.com/datasets/mikhail1681/walmart-sales)
- File used: `walmart_sales.csv`
- Columns: `Store`, `Date`, `Weekly_Sales`, `Holiday_Flag`, `Temperature`, `Fuel_Price`, `CPI`, `Unemployment`

## Notebook Highlights
1. **Exploratory overview** – Inspects schema, summary stats, and missing values.
2. **Data cleaning**
   - Parse `Date` and sort by `Store` then `Date`.
   - Format `Date` as `MM-DD-YYYY` for presentation.
   - Round metrics (`Weekly_Sales`, `Fuel_Price` to 2 decimals; `Temperature` to whole numbers; `CPI` & `Unemployment` to 3 decimals).
   - Validate zero missing values post-cleaning.
3. **Business questions** – Uses pandas summaries and Seaborn visuals to address:
   - Which holidays lift weekly sales the most.
   - Which stores face the lowest/highest unemployment and what drives the gap.
   - CPI vs. weekly sales correlations overall and split by holiday weeks.
   - Why fuel price is tracked and how it relates to other fields.
4. **Key takeaways**
   - Thanksgiving delivers the strongest holiday sales lift, while Christmas lags, likely due to discounts/returns.
   - Regional economic strength (captured by CPI and unemployment) explains most store-to-store differences; stores in high-unemployment markets consistently trail in sales.
   - CPI has only a mild relationship with sales, and fuel price is better viewed as a macro signal than a direct driver of weekly revenue.

## Tools
`pandas`, `numpy`, `matplotlib`, `seaborn`, `dash`, `plotly`

## Dashboard
Turn the notebook insights into an interactive dashboard powered by Dash + Plotly (`app.py`):
- Summary cards highlight coverage, store count, average weekly sales, and the time span.
- Holiday performance bar chart ranks the busiest holiday weeks.
- Store-level scatter plot shows how unemployment and CPI relate to average weekly sales with a selectable store highlight.
- CPI vs. weekly sales scatter plus trendline compares holiday vs. non-holiday weeks.
- Dual-axis line chart tracks fuel price against total weekly sales over time.

### Run the dashboard
1. (Optional) create a virtual environment.
2. Install requirements: `pip install dash plotly pandas numpy`.
3. Launch with `python app.py` and open the printed URL (defaults to http://127.0.0.1:8050/).

## Author
**Iris Shtutman**   
[LinkedIn](https://www.linkedin.com/in/iris-shtutman-b73ba2277/)
