FROM mcr.microsoft.com/playwright/python:v1.52.0-noble


RUN apt-get update && apt-get -y install ffmpeg python3-brotli

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

# Asegúrate de que run_compiled.sh sea ejecutable
RUN chmod +x ./run_compiled.sh

# Este es el script que SIEMPRE se ejecutará primero
ENTRYPOINT ["./run_compiled.sh"]
CMD ["python", "app.py"]
