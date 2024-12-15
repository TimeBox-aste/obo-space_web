FROM python:3.12

# Set the working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port
EXPOSE 8000

# Command to run the application  "-w", "4" 
CMD ["gunicorn", "-b", "0.0.0.0:8000", "main:app"]