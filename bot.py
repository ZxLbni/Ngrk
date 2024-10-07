import logging
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from pyngrok import ngrok, conf
from flask import Flask
import os
import threading

# Flask app initialization for running 24/7
app = Flask(__name__)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace these with your credentials
BOT_TOKEN = os.getenv('BOT_TOKEN', "YOUR_TELEGRAM_BOT_TOKEN")
NGROK_AUTH_TOKEN = os.getenv('NGROK_AUTH_TOKEN', "YOUR_NGROK_AUTH_TOKEN")

# Set up NgROK config
conf.get_default().auth_token = NGROK_AUTH_TOKEN

# Global variable to store active NgROK tunnel
active_tunnel = None

# Command handler for '/start'
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('NgROK Management Bot is running. Use /manage to see available commands.')

# Command handler for '/manage' - Show management options
def manage(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('NgROK Management Options:\n'
                              '/status - Get current tunnel status\n'
                              '/start_tunnel - Start a new NgROK tunnel\n'
                              '/stop_tunnel - Stop the active tunnel\n'
                              '/create_tunnel - Create a custom tunnel\n'
                              '/endpoints - Get current endpoints\n')

# Command handler for '/status' - Show NgROK tunnel status
def status(update: Update, context: CallbackContext) -> None:
    global active_tunnel
    if active_tunnel:
        update.message.reply_text(f"NgROK Tunnel is Active:\nPublic URL: {active_tunnel.public_url}\nLocal Address: {active_tunnel.config['addr']}")
    else:
        update.message.reply_text("No active NgROK tunnel.")

# Command handler for '/start_tunnel' - Start a new NgROK tunnel
def start_tunnel(update: Update, context: CallbackContext) -> None:
    global active_tunnel
    if active_tunnel:
        update.message.reply_text(f"Tunnel already running: {active_tunnel.public_url}")
    else:
        active_tunnel = ngrok.connect(5000)  # Expose local port 5000
        update.message.reply_text(f"Started new NgROK tunnel: {active_tunnel.public_url}")
        logger.info(f"NgROK Tunnel started at {active_tunnel.public_url}")

# Command handler for '/stop_tunnel' - Stop the active NgROK tunnel
def stop_tunnel(update: Update, context: CallbackContext) -> None:
    global active_tunnel
    if active_tunnel:
        ngrok.disconnect(active_tunnel.public_url)  # Disconnect the tunnel
        update.message.reply_text(f"Stopped NgROK tunnel: {active_tunnel.public_url}")
        active_tunnel = None
    else:
        update.message.reply_text("No active NgROK tunnel to stop.")

# Command handler for '/create_tunnel' - Create a custom NgROK tunnel with specified port
def create_tunnel(update: Update, context: CallbackContext) -> None:
    global active_tunnel
    if len(context.args) > 0:
        port = context.args[0]
        if active_tunnel:
            ngrok.disconnect(active_tunnel.public_url)  # Disconnect previous tunnel
        active_tunnel = ngrok.connect(port)  # Create new tunnel with given port
        update.message.reply_text(f"Started new NgROK tunnel on port {port}: {active_tunnel.public_url}")
    else:
        update.message.reply_text("Please provide a port number. Usage: /create_tunnel <port>")

# Command handler for '/endpoints' - List all active NgROK tunnels (endpoints)
def endpoints(update: Update, context: CallbackContext) -> None:
    tunnels = ngrok.get_tunnels()
    if tunnels:
        reply_message = "Current NgROK Endpoints:\n"
        for tunnel in tunnels:
            reply_message += f"Public URL: {tunnel.public_url}, Local Address: {tunnel.config['addr']}\n"
        update.message.reply_text(reply_message)
    else:
        update.message.reply_text("No active NgROK endpoints.")

# Function to set up NgROK tunnel webhook for the bot
def setup_ngrok_webhook(updater: Updater):
    global active_tunnel
    if not active_tunnel:
        active_tunnel = ngrok.connect(5000)  # Start tunnel on port 5000 if not already running
    public_url = active_tunnel.public_url
    webhook_url = public_url + "/webhook"
    updater.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to {webhook_url}")

# Flask route for keeping the server alive
@app.route('/')
def home():
    return "Bot is running!"

# Flask app running in a separate thread
def run_flask():
    app.run(host='0.0.0.0', port=8080)

# Main function
def main():
    # Start Flask in a separate thread to keep the app alive
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    # Set up the Updater and Dispatcher
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("manage", manage))
    dp.add_handler(CommandHandler("status", status))
    dp.add_handler(CommandHandler("start_tunnel", start_tunnel))
    dp.add_handler(CommandHandler("stop_tunnel", stop_tunnel))
    dp.add_handler(CommandHandler("create_tunnel", create_tunnel, pass_args=True))
    dp.add_handler(CommandHandler("endpoints", endpoints))

    # Set up NgROK and webhook
    setup_ngrok_webhook(updater)

    # Start the webhook on port 5000
    updater.start_webhook(listen="0.0.0.0", port=5000, url_path="/webhook")

    logger.info("Bot is running...")

    # Keep the bot running until interrupted
    updater.idle()

if __name__ == '__main__':
    main()
    