# Use an official Python image as the base image
FROM python:3.8-slim-buster

# Set the working directory in the container to /app
WORKDIR /app

# Copy the contents of the current directory to /app
COPY . /app

# Upgrade pip and install necessary packages
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Set the default command to run the Flask app
CMD ["python", "app.py"]