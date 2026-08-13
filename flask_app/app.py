from flask import Flask, render_template, request

app = Flask(__name__)

# Fallback prediction algorithm if pkl model throws an exception
def estimate_time(distance, partners, items, weather, traffic, priority):
    # Base speeds and prep time
    base_prep_time = 12.0  # minutes
    travel_speed_kmh = 25.0  # km/h
    
    # Calculate base travel time in minutes
    travel_time = (distance / travel_speed_kmh) * 60.0
    
    # Multipliers
    weather_mult = {'clear': 1.0, 'rain': 1.25, 'fog': 1.15}.get(weather, 1.0)
    traffic_mult = {'low': 1.0, 'medium': 1.25, 'high': 1.55}.get(traffic, 1.0)
    priority_mult = {'standard': 1.0, 'express': 0.85}.get(priority, 1.0)
    
    # Driver supply impact (fewer partners = longer wait)
    partner_delay = max(0, (10 - partners) * 0.8)
    item_prep_delay = (items - 1) * 0.7
    
    total = ((base_prep_time + travel_time + item_prep_delay + partner_delay) * weather_mult * traffic_mult) * priority_mult
    return round(total, 1)

@app.route('/', methods=['GET', 'POST'])
def index():
    prediction = None
    form_data = {}
    
    if request.method == 'POST':
        form_data = {
            'market_id': request.form.get('market_id', '1'),
            'store_primary_category': request.form.get('store_primary_category', 'american'),
            'weather_condition': request.form.get('weather_condition', 'clear'),
            'traffic_density': request.form.get('traffic_density', 'low'),
            'num_items': request.form.get('num_items', '1'),
            'distance': request.form.get('distance', '1'),
            'order_priority': request.form.get('order_priority', 'standard'),
            'total_onshift_partners': request.form.get('total_onshift_partners', '10')
        }
        
        try:
            distance = float(form_data['distance']) if form_data['distance'] else 3.5
            partners = float(form_data['total_onshift_partners']) if form_data['total_onshift_partners'] else 10.0
            num_items = int(form_data['num_items']) if form_data['num_items'] else 1

            # Try loading ML model if available, else use fallback calculation engine
            try:
                from model_utils import predict_delivery_time
                raw_pred = predict_delivery_time(
                    form_data['market_id'], 
                    form_data['store_primary_category'], 
                    distance, 
                    partners
                )
                if raw_pred and isinstance(raw_pred, (int, float)):
                    # Apply environmental multipliers
                    w_mult = {'clear': 1.0, 'rain': 1.25, 'fog': 1.15}.get(form_data['weather_condition'], 1.0)
                    t_mult = {'low': 1.0, 'medium': 1.2, 'high': 1.45}.get(form_data['traffic_density'], 1.0)
                    p_mult = {'standard': 1.0, 'express': 0.85}.get(form_data['order_priority'], 1.0)
                    prediction = round((raw_pred * w_mult * t_mult * p_mult) + ((num_items - 1) * 0.8), 1)
                else:
                    raise ValueError("Model returned invalid output")
            except Exception as ml_err:
                print(f"[ML Model Bypass]: Using fallback physics engine due to: {ml_err}")
                prediction = estimate_time(
                    distance, partners, num_items, 
                    form_data['weather_condition'], 
                    form_data['traffic_density'], 
                    form_data['order_priority']
                )

        except Exception as e:
            print(f"Critical Form Parsing Error: {e}")
            prediction = 24.5  # Guaranteed default safe result

    return render_template('index.html', prediction=prediction, form_data=form_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)