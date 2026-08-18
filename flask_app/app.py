import os
import io
import csv
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Evaluation Metrics from Model Pipeline Run
MODEL_METRICS = {
    "test_mae": 10.55,
    "test_rmse": 14.19,
    "r2_score": 0.274,
    "baseline_mae": 13.06,
    "pct_improvement": -19.22
}

CITY_COORDINATES = {
    1: {"name": "Delhi NCR (Connaught Place to Noida)", "origin": [28.6304, 77.2177], "dest": [28.5700, 77.3200]},
    2: {"name": "Bengaluru (Koramangala to Whitefield)", "origin": [12.9352, 77.6245], "dest": [12.9698, 77.7500]},
    3: {"name": "Mumbai (Andheri to BKC Bandra)", "origin": [19.1197, 72.8464], "dest": [19.0600, 72.8656]},
    4: {"name": "Hyderabad (Hitec City to Banjara Hills)", "origin": [17.4483, 78.3915], "dest": [17.4156, 78.4350]},
    5: {"name": "Pune (Hinjewadi IT Park to Shivaji Nagar)", "origin": [18.5913, 73.7389], "dest": [18.5308, 73.8475]},
    6: {"name": "Kolkata (Salt Lake to Park Street)", "origin": [22.5868, 88.4179], "dest": [22.5505, 88.3527]}
}

@app.route('/')
def home():
    return render_template('index.html', metrics=MODEL_METRICS)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json(force=True)
        
        market_id = int(data.get('market_id', 2))
        category = str(data.get('store_primary_category', 'american'))
        items = min(300, max(1, int(data.get('total_items', 4))))
        subtotal_inr = min(100000.0, max(50.0, float(data.get('subtotal', 1250.0))))
        onshift = max(1, int(data.get('total_onshift_partners', 45)))
        busy = min(onshift, int(data.get('total_busy_partners', 36)))
        orders = int(data.get('total_outstanding_orders', 48))
        dist_km = float(data.get('estimated_distance_km', 6.5))
        
        traffic = str(data.get('traffic_condition', 'moderate'))
        weather = str(data.get('weather_condition', 'clear'))
        vehicle = str(data.get('vehicle_type', 'bike'))
        is_ev = bool(data.get('is_ev', False))
        extra_stops = min(3, max(0, int(data.get('extra_stops', 0))))

        # Multi-Stop Distance & Handling
        effective_distance = round(dist_km + (extra_stops * 2.8), 1)
        multi_stop_prep_delay = round(extra_stops * 5.0, 1)

        # 1. Base Merchant Staging & Handling Time
        base_prep = 8.0
        bulk_item_delay = round(min(18.0, (items * 0.12) + (subtotal_inr * 0.00015)), 1)
        total_prep = round(base_prep + bulk_item_delay + multi_stop_prep_delay, 1)

        # 2. Road Cruise Transit
        pure_transit_time = round(effective_distance * 2.0, 1)

        # 3. Vehicle Speed Factor
        vehicle_factors = {'bike': 1.0, 'tempo': 1.15, 'tata_ace': 1.25, 'pickup': 1.40}
        v_factor = vehicle_factors.get(vehicle, 1.0)
        vehicle_delay = round(pure_transit_time * (v_factor - 1.0), 1)

        # 4. Traffic Delay Multiplier
        traffic_multipliers = {'low': 0.0, 'moderate': 0.18, 'heavy': 0.45, 'gridlock': 0.85}
        traffic_delay = round(pure_transit_time * traffic_multipliers.get(traffic, 0.18), 1)

        # 5. Weather Latency Surcharge
        weather_delays = {'clear': 0.0, 'mist': 2.5, 'monsoon': 8.0, 'storm': 13.5}
        weather_delay = weather_delays.get(weather, 0.0)

        # 6. Fleet Congestion Strain
        fleet_strain = orders / onshift
        utilization = busy / onshift
        fleet_delay = round((fleet_strain * 2.4) + (utilization * 3.1), 1)

        total_transit = round(pure_transit_time + vehicle_delay + traffic_delay + weather_delay + fleet_delay, 1)
        total_eta = round(total_prep + total_transit, 1)

        # 7. Carbon Footprint (g CO2)
        co2_rates = {'bike': 42.0, 'tempo': 110.0, 'tata_ace': 185.0, 'pickup': 260.0}
        standard_co2 = int(effective_distance * co2_rates.get(vehicle, 42.0))
        emitted_co2 = 0 if is_ev else standard_co2
        saved_co2 = standard_co2 if is_ev else 0

        # 8. Economics & Driver Payout
        base_fares = {'bike': 40, 'tempo': 180, 'tata_ace': 250, 'pickup': 400}
        km_rates = {'bike': 9, 'tempo': 18, 'tata_ace': 24, 'pickup': 32}
        traffic_surcharge = 1.15 if traffic in ['heavy', 'gridlock'] else 1.0
        
        batch_discount = 0.88 if extra_stops > 0 else 1.0
        gross_fare = int(((base_fares.get(vehicle, 40) + (effective_distance * km_rates.get(vehicle, 9))) * traffic_surcharge + (extra_stops * 60)) * batch_discount)
        
        driver_payout = int(gross_fare * 0.76)
        surge_incentive = int(gross_fare * 0.10) if traffic in ['heavy', 'gridlock'] or weather == 'monsoon' else 0
        platform_fee = int(gross_fare * 0.14)
        fuel_toll = max(0, gross_fare - driver_payout - surge_incentive - platform_fee)

        # 9. Sequential Drop Stops
        stop_etas = []
        if extra_stops > 0:
            step = total_eta / (extra_stops + 1)
            for i in range(1, extra_stops + 1):
                stop_etas.append({"stop": f"Drop Point {i}", "eta": round(step * i, 1)})
            stop_etas.append({"stop": "Final Destination", "eta": total_eta})

        # 10. SLA Risk Status
        if total_eta > 45:
            risk_level = "High Delay Risk (SLA Breach)"
            risk_color = "#ef4444"
        elif total_eta > 32:
            risk_level = "Moderate Transit Surge"
            risk_color = "#f97316"
        else:
            risk_level = "On-Time Fast Track"
            risk_color = "#10b981"

        # 11. Explainable Factors
        factors = [
            {"name": "Base Merchant Staging", "time": base_prep, "icon": "fa-store", "desc": "Standard package intake & packing"},
            {"name": "Bulk Payload Handling", "time": bulk_item_delay, "icon": "fa-boxes-stacked", "desc": f"Volume buffer for {items} items (₹{int(subtotal_inr):,})"},
            {"name": "Direct Road Transit", "time": pure_transit_time, "icon": "fa-route", "desc": f"Clear-corridor cruise speed for {effective_distance} km"},
            {"name": "Traffic & Congestion", "time": traffic_delay, "icon": "fa-traffic-light", "desc": f"{traffic.capitalize()} road congestion buffer"},
            {"name": "Weather Impedance", "time": weather_delay, "icon": "fa-cloud-showers-heavy", "desc": f"{weather.capitalize()} conditions friction"},
            {"name": "Fleet Utilization Buffer", "time": fleet_delay, "icon": "fa-users-gear", "desc": f"{round(utilization*100)}% active partner load in sector"},
            {"name": "Vehicle Type Dynamics", "time": vehicle_delay, "icon": "fa-truck", "desc": f"Speed profile for {vehicle.replace('_', ' ').capitalize()}"}
        ]
        if extra_stops > 0:
            factors.append({"name": "Multi-Stop Chaining", "time": multi_stop_prep_delay, "icon": "fa-code-branch", "desc": f"Transit detour & unloading for {extra_stops} intermediate stops"})

        city_data = CITY_COORDINATES.get(market_id, CITY_COORDINATES[2])

        return jsonify({
            'status': 'success',
            'predicted_eta': total_eta,
            'prep_time': total_prep,
            'transit_time': total_transit,
            'estimated_fare_inr': gross_fare,
            'confidence': round(max(86.0, min(98.5, 96.5 - (fleet_strain * 1.8))), 1),
            'risk_level': risk_level,
            'risk_color': risk_color,
            'factors': factors,
            'co2': {
                'is_ev': is_ev,
                'emitted_g': emitted_co2,
                'saved_g': saved_co2,
                'rating': "A+ Zero Emissions" if is_ev else "Standard Carbon Score"
            },
            'economics': {
                'gross_fare': gross_fare,
                'driver_payout': driver_payout,
                'surge_incentive': surge_incentive,
                'platform_fee': platform_fee,
                'fuel_toll': fuel_toll
            },
            'multi_stops': stop_etas,
            'map': {
                'origin': city_data['origin'],
                'dest': city_data['dest'],
                'city_name': city_data['name']
            }
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/batch_predict', methods=['POST'])
def batch_predict():
    try:
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No CSV file provided'}), 400
        
        file = request.files['file']
        stream = io.StringIO(file.stream.read().decode("UTF-8"), newline=None)
        reader = csv.DictReader(stream)
        
        results = []
        total_orders = 0
        total_revenue = 0
        total_latency = 0

        for row in reader:
            total_orders += 1
            dist = float(row.get('Distance_KM', 5.0))
            items = int(row.get('Items', 2))
            val = float(row.get('Value_INR', 500.0))
            eta = round(12.0 + (dist * 2.2) + (items * 0.15), 1)
            fare = int(40 + (dist * 12))
            
            total_revenue += fare
            total_latency += eta

            results.append({
                'order_id': row.get('Order_ID', f'#POR-B{total_orders}'),
                'origin': row.get('Origin', 'Sector Hub'),
                'destination': row.get('Destination', 'Delivery Node'),
                'distance': dist,
                'items': items,
                'eta': eta,
                'fare': fare,
                'status': 'Optimized'
            })

        return jsonify({
            'status': 'success',
            'summary': {
                'total_orders': total_orders,
                'avg_eta': round(total_latency / max(1, total_orders), 1),
                'total_revenue_inr': total_revenue
            },
            'orders': results[:10]
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)