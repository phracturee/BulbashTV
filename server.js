import WebTorrent from 'webtorrent';
import { spawn } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import http from 'http';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(fileURLToPath(import.meta.url));

const client = new WebTorrent();
const PORT = 8888;

console.log(`
=====================================================
     Torrent Stream - Streaming to MPV player     
-----------------------------------------------------
  Usage:                                             
  node server.js <magnet-link> [--episode SXXEYY]    
                                                     
  Example:                                           
  node server.js "magnet:?xt=urn:btih:..."           
  node server.js "magnet:..." --episode S01E02       
=====================================================
`);

let magnetUri = process.argv[2];
let episodePattern = null;

// Parse --episode argument
for (let i = 3; i < process.argv.length; i++) {
    if (process.argv[i] === '--episode' && process.argv[i + 1]) {
        episodePattern = process.argv[i + 1];
        console.log(`Episode pattern: ${episodePattern}`);
        i++; // Skip next argument
    }
}

if (!magnetUri) {
    console.error('Error: Specify a magnet link!');
    console.error('Example: node server.js "magnet:?xt=urn:btih:08ada5a7a6183aae1e09d831df6748d566095a10"');
    process.exit(1);
}

// Encode URL if there are invalid characters
try {
    const url = new URL(magnetUri);
    magnetUri = url.toString();
} catch (e) {
    console.error('Error: Invalid magnet link!');
    process.exit(1);
}

console.log('Adding torrent...');

const torrent = client.add(magnetUri, { path: './downloads' });

let videoFile = null;
let fileIndex = 0;
let serverStarted = false;

torrent.on('metadata', () => {
    clearTimeout(metadataTimeout);
    console.log(`\nMetadata received`);
    console.log(`Torrent: ${torrent.name}`);
    console.log(`Files: ${torrent.files.length}`);

    // Find video file (largest file with video extension)
    const videoExts = ['.mp4', '.mkv', '.avi', '.mov', '.webm', '.wmv', '.m4v'];
    let maxSize = 0;

    // If episode pattern is specified (S01E02), search for exact match
    if (episodePattern) {
        console.log(`Searching for file with pattern: ${episodePattern}`);

        // Extract season and episode from pattern
        // Supported formats: S01E06, S1E6, S1.E6, 1x06, 1x6, Series 6, Episode 6
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

        // Pattern: Series 6 or Episode 6
        if (!season) {
            match = episodePattern.match(/^(?:Series|Episode)\s*(\d+)$/i);
            if (match) {
                season = 1; // Default season 1
                episode = parseInt(match[1]);
            }
        }

        if (season && episode) {
            console.log(`Season: ${season}, Episode: ${episode}`);

            // More precise regex patterns for season/episode extraction
            const seasonEpisodePatterns = [
                // S01E01, S1E1
                /S(\d+)E(\d+)/i,
                // S01.E01, S1.E1 (with dot)
                /S(\d+)\.E(\d+)/i,
                // 1x01, 01x01
                /(\d+)x(\d+)/i,
                // Series 1, Episode 1
                /(?:Series|Episode)\s*(\d+)/i,
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

                        console.log(`Checking: ${file.name} -> S${fileSeason}E${fileEpisode} (looking for S${season}E${episode})`);

                        // Exact match for both season and episode (S01E01 != S01E10)
                        if (fileSeason === season && fileEpisode === episode) {
                            console.log(`Exact match found: ${file.name}`);
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
            console.log(`File with pattern not found, using first video file`);
            console.log(`Files available in torrent:`);
            torrent.files.forEach((file, i) => {
                console.log(`   [${i}] ${file.name} (${(file.length / 1024 / 1024).toFixed(1)} MB)`);
            });
        }
    }

    // If video not found by pattern, use largest file
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

    // If video still not found, use largest file
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
        console.error('Video file not found!');
        client.destroy();
        process.exit(1);
    }

    console.log(`\nVideo file: ${videoFile.name}`);
    console.log(`Playing: ${videoFile.name}`);  // For backend parsing
    console.log(`Size: ${(videoFile.length / 1024 / 1024 / 1024).toFixed(2)} GB`);
    console.log(`File index: ${fileIndex}`);

    // IMPORTANT: Reset torrent download, then select only 1 file
    console.log(`\nDownloading ONLY file ${fileIndex}, canceling others...`);

    // First deselect entire torrent (priorities: 0 = don't download)
    torrent.deselect(0, torrent.pieces.length - 1, 0);
    console.log(`   Entire torrent canceled`);

    // Then select only needed file with high priority
    videoFile.select(10); // Priority 10 (highest)
    console.log(`   [${fileIndex}] ${videoFile.name} - DOWNLOADING (priority 10)`);

    // Log all files for debugging
    console.log(`\nFile list:`);
    torrent.files.forEach((file, i) => {
        const isSelected = (i === fileIndex) ? 'DOWNLOADING' : 'CANCELED';
        console.log(`   [${i}] ${file.name} (${(file.length / 1024 / 1024).toFixed(1)} MB) - ${isSelected}`);
    });

    // Start server immediately after metadata received
    startStreaming();
});

torrent.on('error', (err) => {
    console.error(`\nTorrent error: ${err.message}`);
    console.error('Possible causes:');
    console.error('   - No seeders (0 seeders)');
    console.error('   - Dead torrent');
    console.error('   - Connection issues');
    process.exit(1);
});

// Timeout for metadata (60 seconds)
const metadataTimeout = setTimeout(() => {
    if (!videoFile) {
        console.error('\nMetadata timeout (60s)');
        console.error('Torrent cannot get metadata');
        console.error('Check:');
        console.error('   - Seeder availability');
        console.error('   - Internet connection');
        console.error('   - Tracker status');
        client.destroy();
        process.exit(1);
    }
}, 60000);

function startStreaming() {
    if (serverStarted || !videoFile) return;
    serverStarted = true;

    // Create HTTP server for streaming
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
            console.log(`\nPort ${PORT} is busy`);
        }
    });

    server.listen(PORT, () => {
        const actualPort = server.address().port;
        console.log(`\nServer started: http://localhost:${actualPort}`);
        const streamUrl = `http://localhost:${actualPort}/${fileIndex}`;
        console.log(`\nStream URL: ${streamUrl}`);

        // Wait for buffer to accumulate and launch mpv
        let checkCount = 0;
        const checkBuffer = setInterval(() => {
            checkCount++;
            const downloaded = torrent.downloaded;
            const progress = torrent.progress * 100;

            // Log statistics for frontend (parsing in torrent_manager.py)
            const speed = torrent.downloadSpeed;
            const peers = torrent.numPeers;
            const downloadedMB = (downloaded / 1024 / 1024).toFixed(1);
            const speedMB = (speed / 1024 / 1024).toFixed(2);
            console.log(`\nProgress: ${progress.toFixed(1)}% | Downloaded ${downloadedMB} MB | Peers: ${peers} | Speed ${speedMB} MB/s`);

            // Try to launch MPV under different conditions:
            // 1. Downloaded > 10MB (fast start)
            // 2. Progress > 1% (for large files)
            // 3. After 2nd check (1 second)
            // 4. Timeout 5 seconds
            if (downloaded > 10 * 1024 * 1024 || progress > 1 || checkCount >= 2) {
                clearInterval(checkBuffer);
                console.log(`\nLaunch condition met: downloaded ${(downloaded / 1024 / 1024).toFixed(1)} MB, progress ${progress.toFixed(1)}%, check #${checkCount}`);
                launchMpv(streamUrl, server);
            }
        }, 500); // Check every 500ms

        // Timeout 5 seconds - force launch
        setTimeout(() => {
            clearInterval(checkBuffer);
            if (!mpvLaunched) {
                console.log(`\nForce launch by timeout (5s)`);
                launchMpv(streamUrl, server);
            }
        }, 5000);
    });

    // Statistics - update every 500ms for frontend
    // Add newline at start to separate from MPV output
    setInterval(() => {
        const speed = torrent.downloadSpeed;
        const peers = torrent.numPeers;
        const progress = (torrent.progress * 100).toFixed(1);
        const downloaded = (torrent.downloaded / 1024 / 1024).toFixed(1);
        const speedMB = (speed / 1024 / 1024).toFixed(2);
        console.log(`\nProgress: ${progress}% | Downloaded ${downloaded} MB | Peers: ${peers} | Speed ${speedMB} MB/s`);
    }, 500);
}

let mpvLaunched = false;
let mpvProcess = null;
let lastPlaybackPosition = 0;
let totalDuration = 0;

function launchMpv(streamUrl, server) {
    if (mpvLaunched) return;
    mpvLaunched = true;

    console.log('\n\nLaunching MPV...');

    // MPV inherits stdio so it outputs directly to terminal/log
    mpvProcess = spawn('mpv', [
        streamUrl,
        `--title=${videoFile.name}`,
        '--cache=yes',
        '--cache-secs=30',
        '--keep-open=yes',
        '--input-ipc-server=/tmp/mpv-ipc.sock'
    ], {
        stdio: 'inherit',  // MPV outputs directly
        detached: false
    });

    mpvProcess.on('error', (err) => {
        console.error(`\nMPV error: ${err.message}`);
        console.error('Install MPV: sudo apt install mpv');
        server.close();
        cleanup();
    });

    mpvProcess.on('exit', (code) => {
        console.log('\n\nMPV closed');

        // Check view percentage before deleting
        const downloadPath = path.join('./downloads', videoFile.path);
        const watchPercent = totalDuration > 0 ? (lastPlaybackPosition / totalDuration * 100) : 0;

        console.log(`Watched: ${watchPercent.toFixed(1)}% (${(lastPlaybackPosition/60).toFixed(1)} min of ${(totalDuration/60).toFixed(1)} min)`);

        // If watched >90%, delete file
        if (watchPercent > 90) {
            console.log(`\nFile watched >90%, deleting...`);
            try {
                if (fs.existsSync(downloadPath)) {
                    fs.unlinkSync(downloadPath);
                    console.log(`Deleted: ${downloadPath}`);

                    // Try to delete empty folders
                    const dirPath = path.dirname(downloadPath);
                    try {
                        const files = fs.readdirSync(dirPath);
                        if (files.length === 0) {
                            fs.rmdirSync(dirPath);
                            console.log(`Deleted empty folder: ${dirPath}`);
                        }
                    } catch (e) {
                        // Folder not empty or error
                    }
                } else {
                    console.log(`File not found: ${downloadPath}`);
                }
            } catch (err) {
                console.error(`Delete error: ${err.message}`);
            }
        } else {
            console.log(`File saved (watched ${watchPercent.toFixed(1)}%)`);
        }

        server.close();
        cleanup();
    });
}

function cleanup() {
    console.log('\nCleaning up...');
    clearTimeout(metadataTimeout);
    client.destroy(() => {
        console.log('WebTorrent stopped');
        process.exit(0);
    });
}

process.on('SIGINT', cleanup);
process.on('SIGTERM', cleanup);
