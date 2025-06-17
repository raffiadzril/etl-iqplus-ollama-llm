# Transform Service Dockerfile
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
EXPOSE 5001

# Run the transform service (default untuk standalone mode)
CMD ["python", "transform_service.py"]
