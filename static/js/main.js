var PidId=Math.floor(10000000 + Math.random() * 90000000).toString();
function loadChannel(contentId) {
    const video = document.getElementById('video');
    const videoDiv = document.getElementById('video-div');
    const initialMessage = document.getElementById('initial-message');
    
    // Usar la dirección del servidor Acestream configurada o el host actual por defecto
    const aceStreamServer = localStorage.getItem('aceStreamServer') || `${window.location.hostname}:6878`;
    // Determinar el protocolo a usar
    const aceStreamProtocol = localStorage.getItem('aceStreamProtocol') || 'http';
    const videoSrc = `${aceStreamProtocol}://${aceStreamServer}/ace/manifest.m3u8?id=${contentId}&pid=`+PidId;

    // Mostrar mensaje de carga
    initialMessage.style.display = 'none';
    video.style.display = 'block';
    videoDiv.style.display = 'block';
    
    // Información de depuración
    console.log('Intentando cargar stream desde:', videoSrc);

    // Selección de los botones
    const infoEnlaces = document.getElementById('info_enlaces');

    infoEnlaces.innerHTML = `
        <div class="alert alert-info">
            <p><strong>Enlace remoto:</strong> <a href="${videoSrc}" target="_blank">${videoSrc}</a></p>
            <p><strong>Enlace Acestream:</strong> <a href="acestream://${contentId}" target="_blank">${contentId}</a></p>
            <div id="stream-status">Conectando al stream...</div>
        </div>`;
    
    const streamStatus = document.getElementById('stream-status');

    if (Hls.isSupported()) {
        const hls = new Hls({
            debug: true,  // Activar modo debug
            xhrSetup: function(xhr, url) {
                // Log de todas las solicitudes XHR
                console.log('XHR Request to:', url);
                xhr.addEventListener('load', function() {
                    console.log('XHR Response:', xhr.status, xhr.responseText.substring(0, 100) + '...');
                });
                xhr.addEventListener('error', function() {
                    console.error('XHR Error:', xhr.status);
                    streamStatus.innerHTML = `<span class="text-danger">Error de conexión (${xhr.status}). Intenta con otro servidor o protocolo.</span>`;
                });
            }
        });
        
        // Manejadores de eventos HLS
        hls.on(Hls.Events.MEDIA_ATTACHED, function() {
            console.log('HLS: Media attached');
            streamStatus.innerHTML = 'Conectado al reproductor. Cargando stream...';
        });
        
        hls.on(Hls.Events.MANIFEST_PARSED, function(event, data) {
            console.log('HLS: Manifest parsed, found ' + data.levels.length + ' quality levels');
            streamStatus.innerHTML = 'Stream cargado. Iniciando reproducción...';
            video.play().then(() => {
                console.log('Reproducción iniciada correctamente');
                streamStatus.innerHTML = 'Reproduciendo';
            }).catch(e => {
                console.error('Error al iniciar reproducción:', e);
                streamStatus.innerHTML = `<span class="text-danger">Error al iniciar reproducción: ${e.message}</span>`;
            });
        });
        
        hls.on(Hls.Events.ERROR, function(event, data) {
            console.error('HLS Error:', data);
            if (data.fatal) {
                switch(data.type) {
                    case Hls.ErrorTypes.NETWORK_ERROR:
                        streamStatus.innerHTML = `<span class="text-danger">Error de red: ${data.details}. Intenta con otro servidor o protocolo.</span>`;
                        console.error('Error de red fatal', data);
                        hls.startLoad(); // Intentar reconectar
                        break;
                    case Hls.ErrorTypes.MEDIA_ERROR:
                        streamStatus.innerHTML = `<span class="text-danger">Error de medio: ${data.details}. Intentando recuperarse...</span>`;
                        console.error('Error de medio fatal', data);
                        hls.recoverMediaError(); // Intentar recuperarse
                        break;
                    default:
                        streamStatus.innerHTML = `<span class="text-danger">Error desconocido: ${data.details}</span>`;
                        console.error('Error fatal desconocido', data);
                        hls.destroy();
                        break;
                }
            }
        });
        
        // Cargar el origen
        try {
            hls.loadSource(videoSrc);
            hls.attachMedia(video);
        } catch (e) {
            console.error('Error al cargar el origen HLS:', e);
            streamStatus.innerHTML = `<span class="text-danger">Error al cargar el stream: ${e.message}</span>`;
        }
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // Para navegadores Safari que soportan HLS nativamente
        console.log('Usando soporte HLS nativo');
        streamStatus.innerHTML = 'Usando soporte HLS nativo del navegador...';
        
        video.src = videoSrc;
        video.addEventListener('loadedmetadata', function() {
            console.log('Metadata cargada, iniciando reproducción');
            streamStatus.innerHTML = 'Metadata cargada, iniciando reproducción...';
            video.play().then(() => {
                console.log('Reproducción iniciada correctamente');
                streamStatus.innerHTML = 'Reproduciendo';
            }).catch(e => {
                console.error('Error al iniciar reproducción:', e);
                streamStatus.innerHTML = `<span class="text-danger">Error al iniciar reproducción: ${e.message}</span>`;
            });
        });
        
        video.addEventListener('error', function(e) {
            console.error('Error de video:', video.error);
            streamStatus.innerHTML = `<span class="text-danger">Error de video: ${video.error ? video.error.message : 'Desconocido'}</span>`;
        });
    } else {
        console.error('HLS no soportado');
        streamStatus.innerHTML = '<span class="text-danger">Tu navegador no soporta la reproducción de este video.</span>';
        alert('Tu navegador no soporta la reproducción de este video.');
    }
}

function applyTheme() {
    const body = document.body;
    const icon = document.getElementById('theme-icon');
    const logo = document.querySelector('.logo');

    if (localStorage.getItem('theme') === 'dark') {
        body.classList.add('dark-mode');
        icon.classList.remove('bi-moon');
        icon.classList.add('bi-sun');
        logo.src = "/static/lightlogo.png";
    } else {
        body.classList.remove('dark-mode');
        icon.classList.remove('bi-sun');
        icon.classList.add('bi-moon');
        logo.src = "/static/logo.png";
    }
}

function filterChannels() {
    // Obtener el valor del campo de búsqueda
    var input = document.getElementById('searchInput');
    var filter = input.value.toLowerCase();
    var channelsContainer = document.querySelector('.channels-container');
    var accordionItems = channelsContainer.getElementsByClassName('accordion-item');

    // Iterar sobre todos los elementos de acordeón
    for (var i = 0; i < accordionItems.length; i++) {
        var accordionItem = accordionItems[i];
        var channelItems = accordionItem.getElementsByClassName('channel-item');
        var hasVisibleChannel = false;

        // Iterar sobre todos los canales dentro del acordeón
        for (var j = 0; j < channelItems.length; j++) {
            var channelName = channelItems[j].getElementsByClassName('channel-name')[0];
            var currentProgram = channelItems[j].getElementsByClassName('current-program')[0];
            var nextProgram = channelItems[j].getElementsByClassName('next-program')[0];
            
            var textValue = '';
            if (channelName) {
                textValue += channelName.textContent || channelName.innerText;
            }
            if (currentProgram) {
                textValue += ' ' + (currentProgram.textContent || currentProgram.innerText);
            }
            if (nextProgram) {
                textValue += ' ' + (nextProgram.textContent || nextProgram.innerText);
            }

            if (textValue.toLowerCase().indexOf(filter) > -1) {
                channelItems[j].style.display = "";
                hasVisibleChannel = true;
            } else {
                channelItems[j].style.display = "none";
            }
        }

        // Mostrar u ocultar el acordeón basado en si tiene canales visibles
        if (hasVisibleChannel) {
            accordionItem.style.display = "";
        } else {
            accordionItem.style.display = "none";
        }
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Apply theme
    applyTheme();

    // Actualizar el campo de servidor Acestream con el valor guardado
    const aceStreamServerInput = document.getElementById('aceStreamServer');
    if (aceStreamServerInput) {
        const savedServer = localStorage.getItem('aceStreamServer');
        if (savedServer) {
            aceStreamServerInput.value = savedServer;
        } else {
            // Valor por defecto: hostname actual con puerto 6878
            aceStreamServerInput.value = `${window.location.hostname}:6878`;
        }
    }
    
    // Actualizar el selector de protocolo con el valor guardado
    const aceStreamProtocolSelect = document.getElementById('aceStreamProtocol');
    if (aceStreamProtocolSelect) {
        const savedProtocol = localStorage.getItem('aceStreamProtocol');
        if (savedProtocol) {
            aceStreamProtocolSelect.value = savedProtocol;
        }
    }

    // Manejador para guardar la configuración del servidor Acestream
    const saveSettingsBtn = document.getElementById('saveSettings');
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', function() {
            const aceStreamServer = document.getElementById('aceStreamServer').value.trim();
            const aceStreamProtocol = document.getElementById('aceStreamProtocol').value;
            localStorage.setItem('aceStreamServer', aceStreamServer);
            localStorage.setItem('aceStreamProtocol', aceStreamProtocol);
            alert('Configuración guardada correctamente');
        });
    }

    // Sidebar toggle functionality
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('channels-sidebar');
    const body = document.body;

    // Create overlay element
    const overlay = document.createElement('div');
    overlay.className = 'overlay';
    body.appendChild(overlay);

    // Toggle sidebar
    sidebarToggle.addEventListener('click', function() {
        sidebar.classList.toggle('show');
        overlay.classList.toggle('show');
    });

    // Close sidebar when clicking overlay
    overlay.addEventListener('click', function() {
        sidebar.classList.remove('show');
        overlay.classList.remove('show');
    });

    // Close sidebar when selecting a channel on mobile
    const channelItems = document.querySelectorAll('.channel-item');
    channelItems.forEach(item => {
        item.addEventListener('click', function() {
            if (window.innerWidth < 768) {
                sidebar.classList.remove('show');
                overlay.classList.remove('show');
            }
        });
    });

    // Theme toggle
    document.getElementById('theme-toggle').addEventListener('click', function() {
        const body = document.body;
        const icon = document.getElementById('theme-icon');
        const logo = document.querySelector('.logo');

        body.classList.toggle('dark-mode');

        if (body.classList.contains('dark-mode')) {
            icon.classList.remove('bi-moon');
            icon.classList.add('bi-sun');
            logo.src = "/static/lightlogo.png";
            localStorage.setItem('theme', 'dark');
        } else {
            icon.classList.remove('bi-sun');
            icon.classList.add('bi-moon');
            logo.src = "/static/logo.png";
            localStorage.setItem('theme', 'light');
        }
    });

    const testButton = document.getElementById('testButton');
    const testInput = document.getElementById('testInput');

    testButton.addEventListener('click', function() {
        const channelId = testInput.value.trim(); // Obtiene el valor del campo de texto y elimina espacios en blanco
        if (channelId) {
            loadChannel(channelId); // Llama a la función loadChannel con la ID
        } else {
            alert('Por favor, introduce una ID de canal válida.');
        }
    });


   /* const urlButton = document.getElementById('urlButton');
    const urlInput = document.getElementById('urlInput');

    urlButton.addEventListener('click', function() {
        const channelIds = urlInput.value.trim(); // Obtiene el valor del textarea y elimina espacios en blanco inicial y final
        if (channelIds) {
            const channels = channelIds.split('\n') // Divide el texto en un array usando el salto de línea
                                    .map(line => line.trim()) // Elimina espacios en blanco de cada línea
                                    .filter(line => line); // Filtra líneas vacías
    
            if (channels.length > 0) {
                channels.forEach(channelId => loadChannel(channelId)); // Procesa cada valor llamando a `loadChannel`
            } else {
                alert('Por favor, introduce al menos una URL válida.');
            }
        } else {
            alert('Por favor, introduce al menos una URL válida.');
        }
    });*/


    document.getElementById("descargar_m3u_ace").addEventListener("click", function () {
        const url = "/download/acestream_directos.m3u";
        const link = document.createElement("a");
        link.href = url;
        link.download = "acestream_directos.m3u"; // Puedes especificar un nombre aquí si deseas
        link.click();
    });

    document.getElementById("descargar_m3u_remote").addEventListener("click", function () {
        const url = "/download/web_directos.m3u";
        const link = document.createElement("a");
        link.href = url;
        link.download = "web_directos.m3u"; // Puedes especificar un nombre aquí si deseas
        link.click();
    });


        document.getElementById("descargar_m3u_ace_pelis").addEventListener("click", function () {
        const url = "/download/acestream_pelis.m3u";
        const link = document.createElement("a");
        link.href = url;
        link.download = "acestream_pelis.m3u"; // Puedes especificar un nombre aquí si deseas
        link.click();
    });

    document.getElementById("descargar_m3u_remote_pelis").addEventListener("click", function () {
        const url = "/download/web_pelis.m3u";
        const link = document.createElement("a");
        link.href = url;
        link.download = "web_pelis.m3u"; // Puedes especificar un nombre aquí si deseas
        link.click();
    });

    // Mostrar el campo de búsqueda solo si hay elementos accordion-item
    const channelsAccordion = document.getElementById('channelsAccordion');
    const channelsSection = document.getElementById('channelsSection');
    const accordionItems = channelsAccordion.getElementsByClassName('accordion-item');

    if (accordionItems.length > 0) {
        document.getElementById('searchInput').style.display = 'block';
    } else {
        document.getElementById('searchInput').style.display = 'none';
    }

    // Añadir evento de búsqueda
    document.getElementById('searchInput').addEventListener('keyup', filterChannels);
});