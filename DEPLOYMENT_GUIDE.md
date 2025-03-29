# 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚 Bot Deployment Guide

This guide provides step-by-step instructions for deploying the 𝐕𝐨𝐢𝐝𝐕𝐢𝐒𝐚 Telegram bot on a VPS server.

## Prerequisites

- A VPS with Ubuntu 20.04 or newer
- Root or sudo access
- A domain or subdomain (for webhook setup)
- Telegram Bot Token (from BotFather)

## Step 1: Update and Install Dependencies

```bash
# Update the system
sudo apt update
sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3 python3-pip python3-venv git nginx certbot python3-certbot-nginx

# Optional but recommended: Install PostgreSQL if you want to use a database
sudo apt install -y postgresql postgresql-contrib
```

## Step 2: Set Up the Bot

```bash
# Create a directory for the bot
mkdir -p /opt/voidvisa
cd /opt/voidvisa

# Clone the repository (replace with your actual repository URL)
git clone https://github.com/yourusername/voidvisa.git .

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

Create a `.env` file to store your environment variables:

```bash
nano .env
```

Add the following content, replacing the placeholder values with your actual data:

```
# Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
ADMIN_USER_ID=your_telegram_user_id

# Webhook Configuration (for production)
WEBHOOK_URL=https://your-domain.com
WEBHOOK_PORT=8443
WEBHOOK_LISTEN=0.0.0.0
WEBHOOK_CERT_PATH=/path/to/cert.pem
WEBHOOK_KEY_PATH=/path/to/private.key

# Web App Configuration
FLASK_SECRET_KEY=your_random_secret_key
FLASK_PORT=5000

# Database Configuration (optional)
DATABASE_URL=postgresql://username:password@localhost/voidvisa

# API Keys for Gateways
STRIPE_SECRET_KEY=your_stripe_secret_key
ADYEN_API_KEY=your_adyen_api_key
ADYEN_MERCHANT_ACCOUNT=your_adyen_merchant_account
# Add other gateway API keys as needed
```

## Step 4: Set Up SSL Certificate (for Webhook)

If you're using webhooks, you'll need an SSL certificate:

```bash
# Obtain an SSL certificate with Certbot
sudo certbot --nginx -d your-domain.com

# Copy certificates to a location accessible by the bot (adjust paths as needed)
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem /opt/voidvisa/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem /opt/voidvisa/private.key
sudo chown -R $(whoami):$(whoami) /opt/voidvisa/*.pem /opt/voidvisa/*.key
```

Update your `.env` file with the correct paths to these certificates.

## Step 5: Set Up a Systemd Service

Create a systemd service file to run the bot as a background service:

```bash
sudo nano /etc/systemd/system/voidvisa.service
```

Add the following content:

```
[Unit]
Description=VoidViSa Telegram Bot
After=network.target

[Service]
User=your_username
Group=your_username
WorkingDirectory=/opt/voidvisa
Environment=PATH=/opt/voidvisa/venv/bin
EnvironmentFile=/opt/voidvisa/.env
ExecStart=/opt/voidvisa/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable voidvisa
sudo systemctl start voidvisa
```

Check the status:

```bash
sudo systemctl status voidvisa
```

## Step 6: Set Up Nginx as a Reverse Proxy (Optional)

If you want to serve the web interface on port 80/443:

```bash
sudo nano /etc/nginx/sites-available/voidvisa
```

Add the following configuration:

```
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # For webhook endpoint (adjust the path as needed)
    location /your_bot_token {
        proxy_pass http://127.0.0.1:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Enable the site and restart Nginx:

```bash
sudo ln -s /etc/nginx/sites-available/voidvisa /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Step 7: Security Considerations

1. Set up a firewall:

```bash
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 8443  # Only if you're using this port directly for webhook
sudo ufw enable
```

2. Secure the `.env` file:

```bash
chmod 600 /opt/voidvisa/.env
```

3. Regular Updates:

```bash
# Create an update script
nano /opt/voidvisa/update.sh
```

Add:

```bash
#!/bin/bash
cd /opt/voidvisa
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart voidvisa
```

Make it executable:

```bash
chmod +x /opt/voidvisa/update.sh
```

## Step 8: Monitoring and Logs

View the logs:

```bash
# Live logs
sudo journalctl -fu voidvisa

# Last 100 lines
sudo journalctl -u voidvisa -n 100
```

## Scaling Considerations

For high-traffic bots:

1. **Multiple Instances**: You can run multiple instances of the bot on different servers, all using the same webhook URL.

2. **Load Balancing**: Set up Nginx as a load balancer across multiple instances.

3. **Database Scalability**: Move to a dedicated PostgreSQL server or managed database service.

4. **Caching**: Implement Redis or Memcached for caching frequently accessed data.

## Troubleshooting

1. **Service doesn't start**:
   - Check logs: `sudo journalctl -u voidvisa -n 50`
   - Verify environment variables in `.env`
   - Ensure the bot token is valid

2. **Webhook issues**:
   - Verify your domain is properly pointed to your server
   - Check SSL certificate validity
   - Ensure the webhook URL is accessible from the internet

3. **Permission issues**:
   - Check file permissions on cert files and .env
   - Verify the service is running as the correct user

## Regular Maintenance

1. System updates:
```bash
sudo apt update
sudo apt upgrade -y
```

2. Bot updates:
```bash
/opt/voidvisa/update.sh
```

3. SSL certificate renewal (automated with certbot, but verify):
```bash
sudo certbot renew --dry-run
```