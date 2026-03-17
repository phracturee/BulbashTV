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
║  node server.js <magnet-link> [--episode SXXEYY]      ║
║                                                       ║
║  Пример:                                              ║
║  node server.js "magnet:?xt=urn:btih:..."             ║
║  node server.js "magnet:..." --episode S01E02         ║
╚═══════════════════════════════════════════════════════╝
`);

let magnetUri = process.argv[2];
let episodePattern = null;

// Parse --episode argument
for (let i = 3; i < process.argv.length; i++) {
    if (process.argv[i] === '--episode' && process.argv[i + 1]) {
        episodePattern = process.argv[i + 1];
        console.log(`📺 Episode pattern: ${episodePattern}`);
        i++; // Skip next argument
    }
}

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
    clearTimeout(metadataTimeout);
    console.log(`\n✅ Метаданные получены`);
    console.log(`📊 Торрент: ${torrent.name}`);
    console.log(`📁 Файлов: ${torrent.files.length}`);

    // Ищем видеофайл (самый большой с видео расширением)
    const videoExts = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.wmv', '.m4v'];
    let maxSize = 0;

    // Если указан паттерн эпизода (S01E02), ищем точное совпадение
    if (episodePattern) {
        console.log(`🔍 Поиск файла с паттерном: ${episodePattern}`);

        // Извлекаем сезон и серию из паттерна
        // Поддержка форматов: S01E06, S1E6, S1.E6, 1x06, 1x6, Серия 6, Episode 6
        let season = null, episode = null;
        
        // Pattern: S01E06 or S1E6
        let match = episodePattern.match(/^S(\d+)E(\d+)$/i);
        if (match) {
            season = parseInt(match[1]);
            episode = parseInt(match[2]);
        }
        
        // Pattern: S1.E6 or S01.E06
        if (!season) {
            match = episodePattern.match(/^S(\d+)\.E(\d+)$/i);
            if (match) {
                season = parseInt(match[1]);
                episode = parseInt(match[2]);
            }
        }
        
        // Pattern: 1x06 or 1x6
        if (!season) {
            match = episodePattern.match(/^(\d+)x(\d+)$/i);
            if (match) {
                season = parseInt(match[1]);
                episode = parseInt(match[2]);
            }
        }
        
        // Pattern: Серия 6 or Episode 6
        if (!season) {
            match = episodePattern.match(/^(?:Серия|Episode)\s*(\d+)$/i);
            if (match) {
                season = 1; // Default season 1
                episode = parseInt(match[1]);
            }
        }

        if (season && episode) {
            console.log(`🎯 Сезон: ${season}, Серия: ${episode}`);
            
            // More precise regex patterns for season/episode extraction
            const seasonEpisodePatterns = [
                // S01E01, S1E1
                /S(\d+)E(\d+)/i,
                // S01.E01, S1.E1 (with dot)
                /S(\d+)\.E(\d+)/i,
                // 1x01, 01x01
                /(\d+)x(\d+)/i,
                // Серия 1, Episode 1
                /(?:Серия|Episode)\s*(\d+)/i,
            ];

            for (let i = 0; i < torrent.files.length; i++) {
                const file = torrent.files[i];
                const fileName = file.name;
                const fileNameLower = fileName.toLowerCase();

                // Check if file is a video file
                const ext = path.extname(fileName).toLowerCase();
                if (!videoExts.includes(ext)) continue;

                // Try each pattern for exact season/episode match
                for (const pattern of seasonEpisodePatterns) {
                    const fileMatch = fileName.match(pattern);
                    
                    if (fileMatch) {
                        const fileSeason = parseInt(fileMatch[1]);
                        const fileEpisode = parseInt(fileMatch[2]);

                        console.log(`🔍 Проверка: ${file.name} -> S${fileSeason}E${fileEpisode} (ищем S${season}E${episode})`);

                        // Exact match for both season and episode (S01E01 != S01E10)
                        if (fileSeason === season && fileEpisode === episode) {
                            console.log(`✅ Найдено точное совпадение: ${file.name}`);
                            videoFile = file;
                            fileIndex = i;
                            maxSize = file.length;
                            break;
                        }
                    }
                }
                if (videoFile) break;
            }
        }

        if (!videoFile) {
            console.log(`⚠️ Файл с паттерном не найден, берём первый видеофайл`);
            console.log(`📁 Доступные файлы в торренте:`);
            torrent.files.forEach((file, i) => {
                console.log(`   [${i}] ${file.name} (${(file.length / 1024 / 1024).toFixed(1)} MB)`);
            });
        }
    }

    // Если видео не найдено по паттерну, берём самый большой файл
    if (!videoFile) {
        for (let i = 0; i < torrent.files.length; i++) {
            const file = torrent.files[i];
            const ext = path.extname(file.name).toLowerCase();
            if (videoExts.includes(ext) && file.length > maxSize) {
                videoFile = file;
                fileIndex = i;
                maxSize = file.length;
            }
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
    console.log(`Playing: ${videoFile.name}`);  // For backend parsing
    console.log(`📏 Размер: ${(videoFile.length / 1024 / 1024 / 1024).toFixed(2)} GB`);
    console.log(`📁 Индекс файла: ${fileIndex}`);

    // Запускаем сервер сразу после получения метаданных
    startStreaming();
});

torrent.on('error', (err) => {
    console.error(`\n❌ Ошибка торрента: ${err.message}`);
    console.error('💡 Возможные причины:');
    console.error('   - Нет сидов (0 seeders)');
    console.error('   - Торрент мёртвый');
    console.error('   - Проблемы с подключением');
    process.exit(1);
});

// Timeout for metadata (60 seconds)
const metadataTimeout = setTimeout(() => {
    if (!videoFile) {
        console.error('\n⏱️ Таймаут получения метаданных (60с)');
        console.error('💡 Торрент не может получить метаданные');
        console.error('💡 Проверьте:');
        console.error('   - Наличие сидов (seeders)');
        console.error('   - Подключение к интернету');
        console.error('   - Работает ли трекер');
        client.destroy();
        process.exit(1);
    }
}, 60000);

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
        let checkCount = 0;
        const checkBuffer = setInterval(() => {
            checkCount++;
            const downloaded = torrent.downloaded;
            const progress = torrent.progress * 100;
            
            // Пробуем запустить MPV при разных условиях:
            // 1. Загружено > 20MB (быстрый старт)
            // 2. Прогресс > 3% (для больших файлов)
            // 3. После 3-й проверки (3 секунды)
            // 4. Таймаут 8 секунд
            if (downloaded > 20 * 1024 * 1024 || progress > 3 || checkCount >= 3) {
                clearInterval(checkBuffer);
                console.log(`\n🎬 Условие запуска: загружено ${(downloaded / 1024 / 1024).toFixed(1)} MB, прогресс ${progress.toFixed(1)}%, проверка #${checkCount}`);
                launchMpv(streamUrl, server);
            }
        }, 500); // Проверяем каждые 500мс

        // Таймаут 8 секунд - принудительный запуск
        setTimeout(() => {
            clearInterval(checkBuffer);
            if (!mpvLaunched) {
                console.log(`\n🎬 Принудительный запуск по таймауту (8с)`);
                launchMpv(streamUrl, server);
            }
        }, 8000);
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
    clearTimeout(metadataTimeout);
    client.destroy(() => {
        console.log('✅ WebTorrent остановлен');
        process.exit(0);
    });
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
