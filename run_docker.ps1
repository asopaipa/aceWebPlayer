# Initialize Docker Compose command variable
$DOCKER_COMPOSE_CMD = ""

# Check if docker compose is available
try {
    docker compose version | Out-Null
    $DOCKER_COMPOSE_CMD = "docker compose"
}
catch {
    try {
        docker-compose version | Out-Null
        $DOCKER_COMPOSE_CMD = "docker-compose"
    }
    catch {
        Write-Host "Neither 'docker compose' nor 'docker-compose' are installed."
        exit 1
    }
}

# Ask for the port
$PORT = Read-Host "What port do you want to publish the web on? (5001)"
if ([string]::IsNullOrEmpty($PORT)) {
    $PORT = "5001"
}

# Ask about remote access
$ALLOW_REMOTE_ACCESS = Read-Host "Do you want to allow access through the Internet? (yes/NO)"

# Set environment variable for the port
$env:PORT = $PORT

# Update docker-compose.yml based on remote access choice
if ($ALLOW_REMOTE_ACCESS.ToLower() -eq "yes" -or $ALLOW_REMOTE_ACCESS.ToLower() -eq "y") {
    Write-Host "Configuring remote access..."
    
    # Read the content of docker-compose.yml
    $content = Get-Content "docker-compose.yml" -Raw
    
    # Remove comments from specific lines
    $content = $content -replace '#environment:', 'environment:'
    $content = $content -replace '#  - ALLOW_REMOTE_ACCESS=yes', '  - ALLOW_REMOTE_ACCESS=yes'
    
    # Write the modified content back to the file
    $content | Set-Content "docker-compose.yml"
}
else {
    Write-Host "Remote access not enabled."
}

# Build the Docker image
docker build -t acestream-player .

# Start the container
Invoke-Expression "$DOCKER_COMPOSE_CMD up -d"