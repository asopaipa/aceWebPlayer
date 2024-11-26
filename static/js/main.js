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
    const copyAce = document.getElementById('copy_ace');
    const popupAce = document.getElementById('popup_ace');
    const copyRemote = document.getElementById('copy_remote');
    
    // Función para copiar texto al portapapeles
    copyAce.addEventListener('click', () => {
        const textToCopy = `${contentId}`;
        navigator.clipboard.writeText(textToCopy)
            .then(() => {
                alert('Texto copiado al portapapeles: ' + textToCopy);
            })
            .catch(err => {
                console.error('Error al copiar el texto: ', err);
            });
    });
    // Función para copiar texto al portapapeles
    copyRemote.addEventListener('click', () => {
        navigator.clipboard.writeText(videoSrc)
            .then(() => {
                alert('Texto copiado al portapapeles: ' + textToCopy);
            })
            .catch(err => {
                console.error('Error al copiar el texto: ', err);
            });
    });
    
    // Función para abrir un popup con una URL
    popupAce.addEventListener('click', () => {
        const customProtocolUrl = `acestream://${contentId}`
        window.open(customProtocolUrl, '_blank'); // '_blank' abrirá en una nueva ventana o pestaña
    });


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

    document.getElementById("descargar_m3u_ace").addEventListener("click", function () {
        const url = "/download/default.m3u";
        const link = document.createElement("a");
        link.href = url;
        link.download = "default.m3u"; // Puedes especificar un nombre aquí si deseas
        link.click();
    });

    document.getElementById("descargar_m3u_remote").addEventListener("click", function () {
        const url = "/download/default_remote.m3u";
        const link = document.createElement("a");
        link.href = url;
        link.download = "default_remote.m3u"; // Puedes especificar un nombre aquí si deseas
        link.click();
    });
});
