# Load Service Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.py

# Expose port
EXPOSE 5002

# Run the load service (default untuk standalone mode)
CMD ["python", "load_service.py"]
