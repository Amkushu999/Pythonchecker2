#!/usr/bin/env python3
"""
Flask web application for the HUMBL3 CH3CK4R Bot's web interactions.
"""
import os
import json
import logging
from flask import Flask, request, jsonify, render_template, redirect, url_for
import stripe

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

# Initialize Stripe
stripe_api_key = os.getenv("STRIPE_SECRET_KEY", "")
if stripe_api_key:
    stripe.api_key = stripe_api_key

# Get domain for callbacks
YOUR_DOMAIN = os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else 'localhost:5000'

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', bot_name="HUMBL3 CH3CK4R", author="@amkuush")

@app.route('/create-checkout-session', methods=['GET', 'POST'])
def create_checkout_session():
    """Create a Stripe checkout session for premium subscription purchase"""
    try:
        # Handle both GET and POST methods
        if request.method == 'POST':
            # Get user data from request body
            data = request.get_json()
            user_id = data.get('user_id')
            plan = data.get('plan')
            reference_id = data.get('ref')
        else:
            # Get user data from URL parameters
            user_id = request.args.get('user_id')
            plan = request.args.get('plan')
            reference_id = request.args.get('ref')
        
        if not user_id or not plan:
            return jsonify({"error": "Missing user_id or plan"}), 400
        
        # Define prices based on plan (in cents)
        prices = {
            "basic": {"price": 999, "description": "Basic Tier (1 month)"},
            "silver": {"price": 2499, "description": "Silver Tier (3 months)"},
            "gold": {"price": 4499, "description": "Gold Tier (6 months)"},
            "platinum": {"price": 7999, "description": "Platinum Tier (12 months)"},
        }
        
        if plan not in prices:
            return jsonify({"error": "Invalid plan"}), 400
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': prices[plan]["description"],
                        'description': 'HUMBL3 CH3CK4R Bot Premium Access'
                    },
                    'unit_amount': prices[plan]["price"],
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'https://{YOUR_DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}&user_id={user_id}&plan={plan}&ref={reference_id}',
            cancel_url=f'https://{YOUR_DOMAIN}/cancel',
            metadata={
                'user_id': str(user_id),
                'plan': plan,
                'reference_id': reference_id or ''
            }
        )
        
        # If GET request, redirect to checkout URL
        if request.method == 'GET':
            return redirect(checkout_session.url)
        
        # If POST request, return session details as JSON
        return jsonify({"id": checkout_session.id, "url": checkout_session.url})
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')

    try:
        if not stripe_api_key:
            logger.warning("Stripe API key not configured, skipping webhook verification")
            event = json.loads(payload)
        else:
            # Get webhook secret from environment
            webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
            if webhook_secret:
                event = stripe.Webhook.construct_event(
                    payload, sig_header, webhook_secret
                )
            else:
                logger.warning("Stripe webhook secret not configured, skipping webhook verification")
                event = json.loads(payload)
        
        # Handle the event
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Get metadata
            user_id = session.get('metadata', {}).get('user_id')
            plan = session.get('metadata', {}).get('plan')
            
            if user_id and plan:
                # Process the payment based on the plan
                # This would typically update the user's status in your database
                logger.info(f"Payment completed for user {user_id}, plan: {plan}")
                
                # Import here to avoid circular imports
                from database import Database
                db = Database()
                
                # Calculate premium duration based on plan
                premium_duration = None
                if plan == "basic":  # Basic Tier (1 month)
                    premium_days = 30
                elif plan == "silver":  # Silver Tier (3 months)
                    premium_days = 90
                elif plan == "gold":  # Gold Tier (6 months)
                    premium_days = 180
                elif plan == "platinum":  # Platinum Tier (12 months)
                    premium_days = 365
                elif plan == "weekly":  # Backwards compatibility
                    premium_days = 7
                elif plan == "monthly":  # Backwards compatibility
                    premium_days = 30
                elif plan == "lifetime":  # Backwards compatibility
                    premium_days = 36500  # ~100 years
                else:
                    premium_days = 0
                
                # Update user status
                if premium_days > 0:
                    import time
                    expiry = int(time.time()) + (premium_days * 24 * 60 * 60)
                    db.set_premium(int(user_id), expiry)
                    logger.info(f"Premium status updated for user {user_id}, expires at {expiry}")
                
        return jsonify(success=True)
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        return jsonify(error=str(e)), 500

@app.route('/success')
def success():
    """Payment success page"""
    session_id = request.args.get('session_id')
    user_id = request.args.get('user_id')
    plan = request.args.get('plan')
    
    return render_template('success.html', 
                          session_id=session_id,
                          user_id=user_id,
                          plan=plan,
                          bot_name="HUMBL3 CH3CK4R")

@app.route('/cancel')
def cancel():
    """Payment cancellation page"""
    return render_template('cancel.html', bot_name="HUMBL3 CH3CK4R")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)