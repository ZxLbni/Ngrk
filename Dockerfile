# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 5000 for the Telegram bot and 8080 for Flask
EXPOSE 5000 8080

# Define environment variables for the bot and ngrok tokens
ENV BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN
ENV NGROK_AUTH_TOKEN=YOUR_NGROK_AUTH_TOKEN

# Run the bot script when the container launches
CMD ["python", "./bot.py"]
