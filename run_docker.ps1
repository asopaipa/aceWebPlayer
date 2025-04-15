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


# Preguntar si se quiere usuario
$USUARIO = Read-Host "Si quieres proteger la web con usuario y contraseña, introduce el usuario: "
if ($USUARIO) {
    $CONTRASENYA = Read-Host "Introduce la contraseña: "

    $content = Get-Content "app.py" -Raw
    $content = $content -replace 'USERNAME = ""', "USERNAME = `"$USUARIO`""
    $content = $content -replace 'PASSWORD = ""', "PASSWORD = `"$CONTRASENYA`""
    
    # Write the modified content back to the file
    $content | Set-Content "app.py"

}

# Set environment variable for the port
$env:PORT = $PORT




# Build the Docker image
docker build -t acestream-player .

# Start the container
Invoke-Expression "$DOCKER_COMPOSE_CMD up -d"
