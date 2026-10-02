# Use an official Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy only the necessary files
COPY ./app.py /app/app.py
COPY ./requirements.txt /app/requirements.txt

# Expose Flask port
EXPOSE 5000

# Start the Flask application
CMD ["python", "app.py"]
