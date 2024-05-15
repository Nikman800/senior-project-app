# syntax=docker/dockerfile:1

FROM python:3.11

WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgtk2.0-dev \
    libglib2.0-dev \
    libgl1-mesa-dev \
    libglu1-mesa-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 50505

# Start the application
ENTRYPOINT ["gunicorn", "main:app"]