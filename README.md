# Aachen Termin Bot

A Docker-based bot that automatically checks for available appointments at the Aachen city administration office and sends notifications via Signal messenger

If you don't want to use Signal, but another form of notification, you can easily change the webhook and remove Signal from the compose file!

## Features

- Monitors available appointments for various city services
- Sends notifications through Signal messenger when appointments are found
- Configurable appointment types and notification thresholds
- Runs in Docker with automatic restart

## Prerequisites

- Docker and Docker Compose
- Signal account for notifications
- Signal CLI REST API container (included in compose setup)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/PaxIgnis/aachen-termin-bot-docker.git
cd aachen-termin-bot-docker
```

2. Configure the bot by editing the configuration section in `bot.py`:

```python
# Signal API configuration, change these default values
WEBHOOK_URL = "http://IP:PORT/v2/send"
RECIPIENT_NUMBERS = ["+491231231234","+491231231235"]
SENDING_NUMBER = "+491231231236"

# Appointment configuration
SELECTED_APPOINTMENT_TYPE = 44  # See list below for available types
THRESHOLD_HOURS = 24           # How far in advance to check
APPOINTMENT_AMOUNT = 1         # Number of appointments to book
```

3. Configure how often the bot should check by editing the value in `entrypoint.sh`:

   Update the sleep interval to how many seconds to wait between runs. Default is 300 seconds (5 minutes)

   > **Info**: You need to restart the container every time you edit this file.

## Usage

1. Start the containers:

> **Info**: The Docker image will be built automatically if it doesn't exist yet.

Create the folder for signal configs, make the entrypoint executable, built and run container:

```bash
mkdir signal
chmod +x config/entrypoint.sh
docker compose up -d
```

2. Check logs:

```bash
docker logs -f aachen-termin-bot
```

OR open up the `bot.logs` file.

## Available Appointment Types

The bot supports all of the appointment types currently available. Set `SELECTED_APPOINTMENT_TYPE` to the type you want
Full list is in the `bot.py`.

## Configuration

### Signal API

- Uses signal-cli-rest-api container
- Requires initial Signal account setup
- Port 8084 exposed for API access
  If you havn't used the `signal-cli-rest-api` docker container before, read the documentation on how to setup [here](https://github.com/bbernhard/signal-cli-rest-api)

## Troubleshooting

1. Check container logs:

```bash
docker logs aachen-termin-bot
```

2. Verify Signal API is running:

```bash
docker logs signal-cli
```

3. Set the logging level in `bot.py`:

```python
# Logging configuration
logging.basicConfig(level=logging.INFO)  # Change to DEBUG for more detailed logs
```

3. Common issues:
   - Signal registration incomplete
   - Incorrect webhook URL
   - Missing volume mounts
   - Signal Recipient has hidden number

## Credit

Credit goes to the orginal [aachen-termin-bot](https://github.com/noworneverev/aachen-termin-bot) for the scraping framework setup.
