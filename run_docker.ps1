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
        Write-Host "Ni 'docker compose' ni 'docker-compose' están instalados."
        exit 1
    }
}

# Ask for the port
$PORT = Read-Host "¿En qué puerto quieres que se publique la web? (5001) "
if ([string]::IsNullOrEmpty($PORT)) {
    $PORT = "5001"
}

$PORTACE = Read-Host "¿En qué puerto quieres que se publique el Acestream? (6878) "
if ([string]::IsNullOrEmpty($PORTACE)) {
    $PORTACE = "6878"
}

# Ask about remote access
$ALLOW_REMOTE_ACCESS = Read-Host "¿Quieres permitir el acceso a través de Internet? (sí/NO) "

# Set environment variable for the port
$env:PORT = $PORT
$env:PORTACE = $PORTACE

# Update docker-compose.yml based on remote access choice
if ($ALLOW_REMOTE_ACCESS.ToLower() -eq "si" -or $ALLOW_REMOTE_ACCESS.ToLower() -eq "sí") {
    Write-Host "Configurando acceso remoto..."
    
    # Read the content of docker-compose.yml
    $content = Get-Content "docker-compose.yml" -Raw
    
    # Remove comments from specific lines
    $content = $content -replace '#environment:', 'environment:'
    $content = $content -replace '#  - ALLOW_REMOTE_ACCESS=yes', '  - ALLOW_REMOTE_ACCESS=yes'
    
    # Write the modified content back to the file
    $content | Set-Content "docker-compose.yml"
}
else {
    Write-Host "No se habilita el acceso remoto."
}

# Build the Docker image
docker build -t acestream-player .

# Start the container
Invoke-Expression "$DOCKER_COMPOSE_CMD up -d"
