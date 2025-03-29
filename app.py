#!/usr/bin/env python3
"""
Flask web application for the HUMBL3 CH3CK4R Bot's web interactions.
"""
import os
import json
import time
import uuid
import logging
import secrets
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", secrets.token_hex(16))

# Custom filter for formatting Unix timestamps in templates
@app.template_filter('strftime')
def _jinja2_filter_datetime(unix_timestamp, format="%Y-%m-%d %H:%M:%S"):
    """Convert a Unix timestamp to a formatted string."""
    return time.strftime(format, time.localtime(unix_timestamp))

# PayPal email for payments
PAYPAL_EMAIL = "amkushu999@gmail.com"

# Get domain for callbacks
YOUR_DOMAIN = os.environ.get('REPLIT_DOMAINS', '').split(',')[0] if os.environ.get('REPLIT_DOMAINS') else 'localhost:5000'

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html', bot_name="HUMBL3 CH3CK4R", author="@amkuush")

@app.route('/create-checkout-session', methods=['GET', 'POST'])
def create_checkout_session():
    """Redirect to Telegram admin for premium subscription purchase"""
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
        
        # Define plans
        plans = {
            "basic": "Basic Tier (1 month)",
            "silver": "Silver Tier (3 months)",
            "gold": "Gold Tier (6 months)",
            "platinum": "Platinum Tier (12 months)",
        }
        
        if plan not in plans:
            return jsonify({"error": "Invalid plan"}), 400
        
        # Get admin username from config
        from config import ADMIN_USERNAME
        
        # Create Telegram deep link to message the admin
        telegram_url = f"https://t.me/{ADMIN_USERNAME}?start=buy_{plan}_{reference_id}_{user_id}"
        
        # Redirect to Telegram chat with the admin
        return redirect(telegram_url)
        
    except Exception as e:
        logger.error(f"Error redirecting to admin: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/manual-payment-confirmation', methods=['GET', 'POST'])
def manual_payment_confirmation():
    """Manual payment confirmation page for PayPal payments"""
    user_id = request.args.get('user_id')
    plan = request.args.get('plan')
    payment_ref = request.args.get('ref')
    
    if not user_id or not plan or not payment_ref:
        return jsonify({"error": "Missing required parameters"}), 400
    
    # Store payment details for admin review
    try:
        # Load the existing payment records or create new
        payment_records_file = 'payment_records.json'
        try:
            with open(payment_records_file, 'r') as f:
                payment_records = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            payment_records = {"pending": [], "completed": []}
        
        # Store this payment request as pending
        import time
        payment_records["pending"].append({
            "user_id": user_id,
            "plan": plan, 
            "payment_ref": payment_ref,
            "timestamp": int(time.time()),
            "status": "pending"
        })
        
        # Save the updated records
        with open(payment_records_file, 'w') as f:
            json.dump(payment_records, f, indent=2)
        
        # Show success page with instructions
        return render_template('payment_confirmation.html',
                             user_id=user_id,
                             plan=plan,
                             payment_ref=payment_ref,
                             bot_name="HUMBL3 CH3CK4R")
    
    except Exception as e:
        logger.error(f"Error handling payment confirmation: {str(e)}")
        return jsonify({"error": "An error occurred processing your payment confirmation"}), 500

@app.route('/admin/payments', methods=['GET', 'POST'])
def admin_payments():
    """Admin panel to approve payments"""
    from config import ADMIN_USER_IDS
    
    # Check for admin authentication
    admin_id = request.args.get('admin_id')
    if not admin_id or int(admin_id) not in ADMIN_USER_IDS:
        return jsonify({"error": "Unauthorized access"}), 401
    
    # Process payment approval
    if request.method == 'POST':
        payment_ref = request.form.get('payment_ref')
        action = request.form.get('action')  # 'approve' or 'reject'
        
        if not payment_ref or not action:
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Load payment records
        try:
            with open('payment_records.json', 'r') as f:
                payment_records = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return jsonify({"error": "No payment records found"}), 404
        
        # Find the payment
        payment = None
        for p in payment_records["pending"]:
            if p["payment_ref"] == payment_ref:
                payment = p
                break
        
        if not payment:
            return jsonify({"error": f"Payment with reference {payment_ref} not found"}), 404
        
        # Process the action
        if action == 'approve':
            # Calculate premium duration based on plan
            plan = payment["plan"]
            user_id = payment["user_id"]
            
            # Import here to avoid circular imports
            from database import Database
            db = Database()
            
            # Calculate premium duration based on plan
            if plan == "basic":  # Basic Tier (1 month)
                premium_days = 30
            elif plan == "silver":  # Silver Tier (3 months)
                premium_days = 90
            elif plan == "gold":  # Gold Tier (6 months)
                premium_days = 180
            elif plan == "platinum":  # Platinum Tier (12 months)
                premium_days = 365
            else:
                premium_days = 0
            
            # Update user status
            if premium_days > 0:
                expiry = int(time.time()) + (premium_days * 24 * 60 * 60)
                db.set_premium(int(user_id), expiry)
                logger.info(f"Premium status updated for user {user_id}, plan: {plan}, expires at {expiry}")
                
                # Update payment record
                payment_records["pending"].remove(payment)
                payment["status"] = "completed"
                payment["approved_at"] = int(time.time())
                payment["approved_by"] = admin_id
                payment_records["completed"].append(payment)
                
                # Save updated records
                with open('payment_records.json', 'w') as f:
                    json.dump(payment_records, f, indent=2)
                
                return jsonify({"success": True, "message": f"Payment for user {user_id} approved"})
            return jsonify({"error": "Invalid premium plan duration"}), 400
        else:
            # Reject the payment
            payment_records["pending"].remove(payment)
            payment["status"] = "rejected"
            payment["rejected_at"] = int(time.time())
            payment["rejected_by"] = admin_id
            payment_records["completed"].append(payment)
            
            # Save updated records
            with open('payment_records.json', 'w') as f:
                json.dump(payment_records, f, indent=2)
            
            user_id = payment["user_id"]
            return jsonify({"success": True, "message": f"Payment for user {user_id} rejected"})
    
    # Show pending payments
    try:
        with open('payment_records.json', 'r') as f:
            payment_records = json.load(f)
        pending_payments = payment_records.get("pending", [])
        return render_template('admin_payments.html', 
                              payments=pending_payments,
                              admin_id=admin_id,
                              bot_name="HUMBL3 CH3CK4R")
    except (FileNotFoundError, json.JSONDecodeError):
        # No records yet
        return render_template('admin_payments.html', 
                              payments=[],
                              admin_id=admin_id,
                              bot_name="HUMBL3 CH3CK4R")

@app.route('/payment-success')
def payment_success():
    """Payment success page for completed payments"""
    user_id = request.args.get('user_id')
    plan = request.args.get('plan')
    payment_ref = request.args.get('ref')
    
    return render_template('payment_success.html', 
                          user_id=user_id,
                          plan=plan,
                          payment_ref=payment_ref,
                          bot_name="HUMBL3 CH3CK4R")

@app.route('/cancel')
def cancel():
    """Payment cancellation page"""
    return render_template('cancel.html', bot_name="HUMBL3 CH3CK4R")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)