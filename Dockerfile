FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

# Make the entrypoint script executable
RUN chmod +x entrypoint.sh

# Run the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]