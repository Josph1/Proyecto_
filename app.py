from flask import Flask, render_template, request
import pandas as pd
from sklearn.linear_model import LogisticRegression
app = Flask(__name__)

def get_yearly_averages(df):
    yearly_averages = df.groupby('year')['count'].mean().to_dict()
    return yearly_averages

@app.route('/', methods=['GET', 'POST'])
def home():
    xls = pd.ExcelFile('MainData.xlsx')
    sheet_names = xls.sheet_names  
    df = pd.concat(pd.read_excel(xls, sheet) for sheet in sheet_names)
    crimes = df['Highest incidence crimes'].unique().tolist()

    if request.method == 'POST':
        province = request.form.get('province')
        crime = request.form.get('crime')
        year = int(request.form.get('year'))

        df = pd.read_excel(xls, province)
        df = df.melt(id_vars=['Highest incidence crimes'], var_name='date', value_name='count')
        df['date'] = pd.to_datetime(df['date'], format='%b-%y')
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        crime_df = df[df['Highest incidence crimes'] == crime]
        X = crime_df[['year', 'month']]
        y = crime_df['count']
        model = LogisticRegression(max_iter=2000)
        model.fit(X, y)
        future_months = pd.DataFrame({'year': [year]*12, 'month': list(range(1, 13))})
        future_counts = model.predict(future_months).tolist()

        # Calculate yearly totals
        yearly_averages = get_yearly_averages(df)
        predicted_year_average_year = str(year)
        predicted_year_average = sum(future_counts) / len(future_counts)

        # Create date labels for the plot
        start_date = df['date'].min()
        end_date = df['date'].max()
        dates = pd.date_range(start_date, end_date, freq='M')
        dates = dates.strftime('%b-%Y').tolist()
        future_dates = pd.date_range(f"{year}-01", f"{year}-12", freq='M')
        future_dates = future_dates.strftime('%b-%Y').tolist()
        
        # Convert the data to JSON
        data = {
            'x1': X['year'].tolist(),
            'y1': X['month'].tolist(),
            'z1': y.tolist(),
            'x2': future_months['year'].tolist(),
            'y2': future_months['month'].tolist(),
            'dates': dates + future_dates,
            'actual': y.tolist(),
            'predicted': future_counts,
            'yearly_averages': yearly_averages,
            'predicted_year_average_year': predicted_year_average_year,
            'predicted_year_average': predicted_year_average
        }
        return render_template('index.html', province=province, crime=crime, data=data, provinces=sheet_names, crimes=crimes)

    return render_template('index.html', provinces=sheet_names, crimes=crimes, data={})

if __name__ == "__main__":
    app.run(debug=True)
