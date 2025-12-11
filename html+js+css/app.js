// State
let srtFiles = []; // { filename: string, content: string }
let excelData = []; // Array of row objects
let isSrtReady = false;
let isExcelReady = false;

// DOM Elements
const srtInput = document.getElementById('srt-input');
const excelInput = document.getElementById('excel-input');
const srtStatus = document.getElementById('srt-status');
const excelStatus = document.getElementById('excel-status');
const searchSection = document.getElementById('search-section');
const searchInput = document.getElementById('search-input');
const searchBtn = document.getElementById('search-btn');
const resultsList = document.getElementById('results-list');
const resultCount = document.getElementById('result-count');
const loadingIndicator = document.getElementById('loading-indicator');

// Event Listeners
srtInput.addEventListener('change', handleSrtFolderSelect);
excelInput.addEventListener('change', handleExcelSelect);
searchBtn.addEventListener('click', performSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') performSearch();
});

// --- File Handling Functions ---

async function handleSrtFolderSelect(e) {
    const files = Array.from(e.target.files).filter(f => f.name.toLowerCase().endsWith('.srt'));

    if (files.length === 0) {
        updateStatus(srtStatus, 'SRT dosyası bulunamadı', 'error');
        isSrtReady = false;
        checkReady();
        return;
    }

    setLoading(true);
    updateStatus(srtStatus, `${files.length} dosya yükleniyor...`, 'waiting');

    srtFiles = [];

    // Read all files (might take a moment for many files)
    // We use a Promise.all to read them in parallel
    const readPromises = files.map(file => readFileAsText(file));

    try {
        const contents = await Promise.all(readPromises);

        // Zip contents with filenames
        srtFiles = files.map((file, i) => ({
            filename: file.name,
            content: contents[i]
        }));

        updateStatus(srtStatus, `${files.length} SRT yüklendi`, 'success');
        isSrtReady = true;
    } catch (err) {
        console.error(err);
        updateStatus(srtStatus, 'Dosya okuma hatası', 'error');
        isSrtReady = false;
    } finally {
        setLoading(false);
        checkReady();
    }
}

async function handleExcelSelect(e) {
    const file = e.target.files[0];
    if (!file) {
        isExcelReady = false;
        checkReady();
        return;
    }

    setLoading(true);
    updateStatus(excelStatus, 'Okunuyor...', 'waiting');

    try {
        const data = await readFileAsArrayBuffer(file);
        const workbook = XLSX.read(data, { type: 'array' });
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(firstSheet);

        // Normalize keys (trim spaces)
        excelData = jsonData.map(row => {
            const newRow = {};
            for (const key in row) {
                newRow[key.trim()] = row[key];
            }
            return newRow;
        });

        updateStatus(excelStatus, `${excelData.length} satır yüklendi`, 'success');
        isExcelReady = true;
    } catch (err) {
        console.error(err);
        updateStatus(excelStatus, 'Excel okuma hatası', 'error');
        isExcelReady = false;
    } finally {
        setLoading(false);
        checkReady();
    }
}

function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(e);
        // Fallback for encoding could be needed, but assuming UTF-8 or standard for now
        // If needed, we could try readAsText(file, 'ISO-8859-9') for Turkish if UTF-8 fails
        reader.readAsText(file);
    });
}

function readFileAsArrayBuffer(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(e);
        reader.readAsArrayBuffer(file);
    });
}

function updateStatus(element, text, type) {
    element.textContent = text;
    element.className = 'status-badge ' + type;
}

function setLoading(isLoading) {
    if (isLoading) {
        loadingIndicator.classList.remove('hidden');
    } else {
        loadingIndicator.classList.add('hidden');
    }
}

function checkReady() {
    if (isSrtReady && isExcelReady) {
        searchSection.classList.remove('disabled');
        // Optional: Auto focus search
        // searchInput.focus();
    } else {
        searchSection.classList.add('disabled');
    }
}

// --- Search Logic ---

function performSearch() {
    const query = searchInput.value.toLowerCase().trim();
    if (!query) return;

    resultsList.innerHTML = '';
    resultCount.textContent = 'Aranıyor...';

    // Defer to next tick to allow UI to update if synchronous
    setTimeout(() => {
        const results = searchInSrts(query);
        displayResults(results);
    }, 10);
}

function searchInSrts(query) {
    const results = [];

    for (const fileData of srtFiles) {
        const blocks = parseSrtBlocks(fileData.content);

        for (const block of blocks) {
            if (block.text.toLowerCase().includes(query)) {
                results.push({
                    filename: fileData.filename,
                    timestamp: block.startTime,
                    seconds: parseTimestampToSeconds(block.startTime),
                    text: block.text
                });
            }
        }
    }
    return results;
}

function parseSrtBlocks(content) {
    // Normalize newlines
    content = content.replace(/\r\n/g, '\n');
    const blocksRaw = content.split('\n\n');
    const parsedBlocks = [];

    for (const block of blocksRaw) {
        const lines = block.split('\n');
        if (lines.length >= 3) {
            // lines[0] index (optional check)
            // lines[1] time --> time
            const timeLine = lines[1];
            if (timeLine && timeLine.includes('-->')) {
                const startTime = timeLine.split('-->')[0].trim();
                // Join remaining lines as text
                const textLines = lines.slice(2).join(' ');
                const cleanText = textLines.replace(/<[^>]*>/g, '').trim(); // Remove HTML tags

                parsedBlocks.push({
                    startTime: startTime,
                    text: cleanText
                });
            }
        }
    }
    return parsedBlocks;
}

function parseTimestampToSeconds(timeStr) {
    // 00:00:02,230 -> seconds
    timeStr = timeStr.replace(',', '.');
    const parts = timeStr.split(':');
    if (parts.length === 3) {
        const h = parseFloat(parts[0]);
        const m = parseFloat(parts[1]);
        const s = parseFloat(parts[2]);
        return Math.floor(h * 3600 + m * 60 + s);
    }
    return 0;
}

// --- Display Logic ---

function displayResults(results) {
    resultsList.innerHTML = '';
    resultCount.textContent = `${results.length} sonuç bulundu.`;

    if (results.length === 0) {
        resultsList.innerHTML = '<div class="empty-state">Sonuç bulunamadı.</div>';
        return;
    }

    results.forEach(item => {
        const card = document.createElement('div');
        card.className = 'result-card';

        const videoUrl = getVideoUrl(item.filename, item.seconds);

        card.innerHTML = `
            <div class="result-header">
                <span class="result-title">${item.filename}</span>
                <span class="result-time">${item.timestamp}</span>
            </div>
            <div class="result-text">${highlightText(item.text, searchInput.value)}</div>
            <div class="result-actions">
                ${videoUrl ?
                `<a href="${videoUrl}" target="_blank" class="btn primary" style="text-decoration:none; font-size: 0.9em;">İzle (Yeni Sekme)</a>` :
                `<button class="btn secondary" disabled title="Video URL Excel'de bulunamadı">Video Bulunamadı</button>`
            }
            </div>
        `;
        resultsList.appendChild(card);
    });
}

function highlightText(text, query) {
    const regex = new RegExp(`(${escapeRegExp(query)})`, 'gi');
    return text.replace(regex, '<span style="background-color: #f1c40f; color: #000;">$1</span>');
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// --- Video URL Logic ---

function getVideoUrl(filename, seconds) {
    // Logic matched from Python:
    // 1. Extract Episode Number from filename (e.g. "Ep 1", "1. Bölüm", etc)
    // 2. Search Title column in EXCEL for that number

    // Regex to find number: "1. Bölüm" or just digits
    const match = filename.match(/(\d+)\.\s*Bölüm/i);
    if (!match) return null; // Fallback? Current python only does this match

    const episodeNum = match[1]; // String "1"

    // Find in Excel
    const row = excelData.find(r => {
        const title = (r['Title'] || '').toString();
        // Regex: (?<!\d)1\.\s*Bölüm
        // Need to construct regex dynamically
        const pattern = new RegExp(`(?<!\\d)${episodeNum}\\.\\s*Bölüm`, 'i');
        return pattern.test(title);
    });

    if (row && row['Video url']) {
        let url = row['Video url'];
        const separator = url.includes('?') ? '&' : '?';
        return `${url}${separator}t=${seconds}s`;
    }

    return null;
}
