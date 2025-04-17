FROM mcr.microsoft.com/playwright/python:v1.51.0-noble

RUN apt-get update && apt-get -y install ffmpeg

# Set working directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create resources directory if it doesn't exist
RUN mkdir -p resources

# Expose port 5000
EXPOSE 5000

# Load environment variables from .env file
ENV DEFAULT_M3U_PATH=${DEFAULT_M3U_PATH}
ENV EPG_XML_PATH=${EPG_XML_PATH}

# Command to run the application
CMD ["python", "app.py"]
