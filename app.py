from flask import Flask, Response, make_response, request
from flask_cors import CORS
import pandas as pd
import requests 
import json
app = Flask(__name__)
cors = CORS(app)

@app.route("/getState", methods=['GET'])
def getPlotCSV():
    state_code = request.args.get('state')
    death_lag = request.args.get('deathlag')
    if death_lag == None: 
        death_lag = 3
    if state_code == None: 
        state_code = 'National'
    data = requests.get('https://covidtracking.com/api/v1/states/daily.json')
    data = json.loads(data.text)
    state_df = get_state_information(data, state=state_code, death_lag=death_lag)
    resp = make_response(state_df.to_csv())
    resp.headers["Content-Disposition"] = "attachment; filename=covid_data.csv"
    resp.headers["Content-Type"] = "text/csv"
    return resp

def parse_date(date):
    return str(int(date/10000)) + '-' + str(int((date%10000)/100)) + '-' + str(int(date%100))

def get_state_information(data, state='MA', death_lag=3): 
    json_df = pd.DataFrame.from_records(data)
    state_df = get_information_about_state(json_df, state, death_lag)
    return state_df
    

def get_information_about_state(dataframe, state_code='NY', death_lag=3):
    if state_code == 'National':
        return dataframe
    dataframe = dataframe[['date', 'state', 'positive', 'negative', 'death', 'positiveIncrease', 'negativeIncrease']]
    state_df = dataframe.loc[dataframe['state'] == state_code]
    state_df['date']= pd.to_datetime(state_df['date'].apply(parse_date))
    state_df = state_df.drop_duplicates('negative')
    state_df['pt_ratio'] = state_df['positive']/(state_df['positive'] + state_df['negative'])
    state_df['positiveIncrease'] = state_df['positive'] - state_df['positive'].shift(-1)
    state_df['negativeIncrease'] = state_df['negative'] - state_df['negative'].shift(-1)
    
    state_df['pt_increase_ratio'] = state_df['positiveIncrease']/(state_df['positiveIncrease'] 
                                                                  + state_df['negativeIncrease'])
    state_df['death_lag'] = state_df['death'].shift(death_lag)
    state_df['death_ratio_lag'] = state_df['death']/state_df['positiveIncrease']
    state_df = state_df.fillna(0)
    state_df = state_df[:-9]
    return state_df
 
if __name__ == "__main__":
     app.run(host='0.0.0.0')