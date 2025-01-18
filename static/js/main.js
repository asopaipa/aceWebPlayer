var PidId=Math.floor(10000000 + Math.random() * 90000000).toString();
function loadChannel(contentId) {
    const video = document.getElementById('video');
    const videoDiv = document.getElementById('video-div');
    const initialMessage = document.getElementById('initial-message');
    const videoSrc = `http://${window.location.hostname}:6878/ace/manifest.m3u8?id=${contentId}&pid=`+PidId;

    initialMessage.style.display = 'none';
    video.style.display = 'block';
    videoDiv.style.display = 'block';

    // Selección de los botones
    const infoEnlaces = document.getElementById('info_enlaces');

    infoEnlaces.innerHTML = `Enlace remoto: <a href="${videoSrc}" target="_blank">${videoSrc}</a><br>Enlace Acestream: <a href="acestream://${contentId}" target="_blank">${contentId}</a>`;

    if (Hls.isSupported()) {
        const hls = new Hls();
        hls.loadSource(videoSrc);
        hls.attachMedia(video);
        hls.on(Hls.Events.MANIFEST_PARSED, function() {
            video.play();
        });
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        video.src = videoSrc;
        video.addEventListener('loadedmetadata', function() {
            video.play();
        });
    } else {
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


    const urlButton = document.getElementById('urlButton');
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
    });


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
