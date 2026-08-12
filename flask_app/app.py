from flask import Flask, render_template, request
from model_utils import predict_delivery_time

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    prediction = None
    form_data = {}
    
    if request.method == 'POST':
        form_data = {
            'market_id': request.form.get('market_id', ''),
            'store_primary_category': request.form.get('store_primary_category', ''),
            'distance': request.form.get('distance', ''),
            'total_onshift_partners': request.form.get('total_onshift_partners', '')
        }
        
        input_data = {
            'market_id': form_data['market_id'],
            'store_primary_category': form_data['store_primary_category'],
            'distance': float(form_data['distance']) if form_data['distance'] else 0.0,
            'total_onshift_partners': int(form_data['total_onshift_partners']) if form_data['total_onshift_partners'] else 0
        }
        
        prediction = predict_delivery_time(input_data)
        
    return render_template('index.html', prediction=prediction, form_data=form_data)

if __name__ == '__main__':
    app.run(debug=True)