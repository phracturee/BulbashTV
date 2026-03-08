import WebTorrent from 'webtorrent';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import http from 'http';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const client = new WebTorrent();
const PORT = 8888;

console.log(`
╔═══════════════════════════════════════════════════════╗
║     🍿 Torrent Stream MPV - Стриминг в MPV плеер     ║
╠═══════════════════════════════════════════════════════╣
║  Использование:                                       ║
║  node server.js <magnet-link>                         ║
║                                                       ║
║  Пример:                                              ║
║  node server.js "magnet:?xt=urn:btih:..."             ║
╚═══════════════════════════════════════════════════════╝
`);

let magnetUri = process.argv[2];

if (!magnetUri) {
    console.error('❌ Укажите magnet-ссылку!');
    console.error('Пример: node server.js "magnet:?xt=urn:btih:08ada5a7a6183aae1e09d831df6748d566095a10"');
    process.exit(1);
}

// Кодируем ссылку если есть некорректные символы
try {
    const url = new URL(magnetUri);
    magnetUri = url.toString();
} catch (e) {
    console.error('❌ Некорректная magnet-ссылка!');
    process.exit(1);
}

console.log('📥 Добавление торрента...');

const torrent = client.add(magnetUri, { path: './downloads' });

let videoFile = null;
let fileIndex = 0;
let serverStarted = false;

torrent.on('metadata', () => {
    console.log(`\n✅ Метаданные получены`);
    console.log(`📊 Торрент: ${torrent.name}`);
    console.log(`📁 Файлов: ${torrent.files.length}`);

    // Ищем видеофайл (самый большой с видео расширением)
    const videoExts = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.wmv', '.m4v'];
    let maxSize = 0;

    for (let i = 0; i < torrent.files.length; i++) {
        const file = torrent.files[i];
        const ext = path.extname(file.name).toLowerCase();
        if (videoExts.includes(ext) && file.length > maxSize) {
            videoFile = file;
            fileIndex = i;
            maxSize = file.length;
        }
    }

    // Если видео не найдено, берём самый большой файл
    if (!videoFile) {
        for (let i = 0; i < torrent.files.length; i++) {
            const file = torrent.files[i];
            if (file.length > maxSize) {
                videoFile = file;
                fileIndex = i;
                maxSize = file.length;
            }
        }
    }

    if (!videoFile) {
        console.error('❌ Видеофайл не найден!');
        client.destroy();
        process.exit(1);
    }

    console.log(`\n🎬 Видеофайл: ${videoFile.name}`);
    console.log(`📏 Размер: ${(videoFile.length / 1024 / 1024 / 1024).toFixed(2)} GB`);
    
    // Запускаем сервер сразу после получения метаданных
    startStreaming();
});

torrent.on('error', (err) => {
    console.error(`\n❌ Ошибка торрента: ${err.message}`);
    process.exit(1);
});

function startStreaming() {
    if (serverStarted || !videoFile) return;
    serverStarted = true;

    // Создаём HTTP сервер для стриминга
    const server = http.createServer((req, res) => {
        const urlPath = req.url.replace(/^\//, '');
        
        if (urlPath !== String(fileIndex)) {
            res.writeHead(404);
            res.end('Not found');
            return;
        }

        const ext = path.extname(videoFile.name).toLowerCase();
        const contentTypes = {
            '.mp4': 'video/mp4',
            '.mkv': 'video/x-matroska',
            '.avi': 'video/x-msvideo',
            '.webm': 'video/webm',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.m4v': 'video/x-m4v'
        };
        const contentType = contentTypes[ext] || 'application/octet-stream';

        const range = req.headers.range;
        if (range) {
            const positions = range.replace(/bytes=/, '').split('-');
            const start = parseInt(positions[0], 10);
            const end = positions[1] ? parseInt(positions[1], 10) : videoFile.length - 1;
            const chunkSize = end - start + 1;

            res.writeHead(206, {
                'Content-Range': `bytes ${start}-${end}/${videoFile.length}`,
                'Accept-Ranges': 'bytes',
                'Content-Length': chunkSize,
                'Content-Type': contentType
            });

            const stream = videoFile.createReadStream({ start, end });
            stream.on('error', () => {});
            stream.pipe(res);
            res.on('error', () => {});
        } else {
            res.writeHead(200, {
                'Content-Length': videoFile.length,
                'Content-Type': contentType
            });
            const stream = videoFile.createReadStream();
            stream.on('error', () => {});
            stream.pipe(res);
            res.on('error', () => {});
        }
    });

    server.on('error', (err) => {
        if (err.code === 'EADDRINUSE') {
            console.log(`\n⚠️ Порт ${PORT} занят`);
        }
    });

    server.listen(PORT, () => {
        const actualPort = server.address().port;
        console.log(`\n🌐 Сервер запущен: http://localhost:${actualPort}`);
        const streamUrl = `http://localhost:${actualPort}/${fileIndex}`;
        console.log(`\n📺 URL потока: ${streamUrl}`);
        
        // Ждём накопления буфера и запускаем mpv
        const checkBuffer = setInterval(() => {
            const downloaded = torrent.downloaded;
            // Ждём пока загрузится хотя бы 50MB или пройдёт 10 секунд
            if (downloaded > 50 * 1024 * 1024) {
                clearInterval(checkBuffer);
                launchMpv(streamUrl, server);
            }
        }, 1000);
        
        // Таймаут 15 секунд
        setTimeout(() => {
            clearInterval(checkBuffer);
            if (!mpvLaunched) {
                launchMpv(streamUrl, server);
            }
        }, 15000);
    });

    // Статистика
    setInterval(() => {
        const speed = torrent.downloadSpeed;
        const peers = torrent.numPeers;
        const progress = (torrent.progress * 100).toFixed(1);
        const downloaded = (torrent.downloaded / 1024 / 1024).toFixed(1);
        process.stdout.write(`\r📊 Прогресс: ${progress}% | ⬇ ${downloaded} MB | 📶 Пиров: ${peers} | ⚡ ${(speed / 1024 / 1024).toFixed(2)} MB/s   `);
    }, 1000);
}

let mpvLaunched = false;

function launchMpv(streamUrl, server) {
    if (mpvLaunched) return;
    mpvLaunched = true;
    
    console.log('\n\n🎬 Запуск MPV...');
    
    const mpv = spawn('mpv', [
        streamUrl,
        `--title=${videoFile.name}`,
        '--cache=yes',
        '--cache-secs=30',
        '--keep-open=yes'
    ], {
        stdio: 'inherit',
        detached: false
    });

    mpv.on('error', (err) => {
        console.error(`\n❌ Ошибка MPV: ${err.message}`);
        console.error('Установите MPV: sudo apt install mpv');
        server.close();
        cleanup();
    });

    mpv.on('exit', () => {
        console.log('\n\n👋 MPV закрыт');
        server.close();
        cleanup();
    });
}

function cleanup() {
    console.log('\n🧹 Остановка...');
    client.destroy(() => {
        console.log('✅ WebTorrent остановлен');
        process.exit(0);
    });
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
