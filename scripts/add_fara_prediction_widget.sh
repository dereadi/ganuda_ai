#!/bin/bash
# FARA Prediction Widget Installation Script
# Run on goldfish (192.168.132.223) where SAG lives
# Usage: bash /ganuda/scripts/add_fara_prediction_widget.sh

set -e
SAG_APP=/ganuda/home/dereadi/sag_unified_interface/app.py

echo '=== FARA Prediction Widget Installer ==='
echo ''

# Step 1: Backup app.py
echo '[1/4] Backing up app.py...'
cp $SAG_APP ${SAG_APP}.bak.$(date +%Y%m%d_%H%M%S)
echo 'Backup created'

# Step 2: Check if route already exists
if grep -q 'def fara_prediction' $SAG_APP; then
    echo 'Route already exists, skipping insertion'
else
    # Step 3: Create temp file with new route
    echo '[2/4] Creating prediction route...'
    cat > /tmp/fara_pred_route.txt << 'ROUTEEOF'

@app.route('/api/fara/prediction')
def fara_prediction():
    """Get current FARA prediction from thermal memory."""
    try:
        conn = psycopg2.connect(
            host='192.168.132.222',
            database='triad_federation',
            user='claude',
            password='jawaseatlasers2'
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT current_category, predicted_category, confidence, prediction_timestamp
            FROM fara_predictions
            ORDER BY prediction_timestamp DESC
            LIMIT 1
        """)
        row = cur.fetchone()
        conn.close()
        if row:
            return jsonify({
                'current': row[0],
                'predicted': row[1],
                'confidence': float(row[2]) * 100 if row[2] else 0,
                'timestamp': row[3].isoformat() if row[3] else None
            })
        return jsonify({'current': 'unknown', 'predicted': 'unknown', 'confidence': 0, 'note': 'no predictions yet'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

ROUTEEOF

    # Step 4: Find fara_query route and insert before it
    echo '[3/4] Inserting route into app.py...'
    LINE=$(grep -n 'def fara_query' $SAG_APP | head -1 | cut -d: -f1)
    if [ -n "$LINE" ]; then
        # Insert 2 lines before fara_query (to get before @app.route decorator)
        INSERT_LINE=$((LINE - 2))
        head -n $INSERT_LINE $SAG_APP > /tmp/app_new.py
        cat /tmp/fara_pred_route.txt >> /tmp/app_new.py
        tail -n +$((INSERT_LINE + 1)) $SAG_APP >> /tmp/app_new.py
        cp /tmp/app_new.py $SAG_APP
        echo "Route inserted before line $LINE"
    else
        echo 'Could not find fara_query, appending to end'
        cat /tmp/fara_pred_route.txt >> $SAG_APP
    fi
fi

# Step 5: Restart SAG
echo '[4/4] Restarting SAG...'
pkill -f 'sag_unified_interface/app.py' || true
sleep 2
cd /ganuda/home/dereadi/sag_unified_interface
nohup /ganuda/home/dereadi/cherokee_venv/bin/python3 app.py > /tmp/sag.log 2>&1 &
sleep 3

# Verify
echo ''
echo '=== Verification ==='
RESULT=$(curl -s http://localhost:4000/api/fara/prediction)
echo $RESULT
echo ''
if echo $RESULT | grep -q 'current'; then
    echo 'SUCCESS! Endpoint is working.'
else
    echo 'ERROR - Check /tmp/sag.log for details'
    tail -20 /tmp/sag.log
fi
echo ''
echo 'Web: http://192.168.132.223:4000/api/fara/prediction'
