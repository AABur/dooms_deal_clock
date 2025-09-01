/**
 * API base URL configuration - switches between development and production endpoints
 * @type {string}
 */
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api' 
    : '/api';
/**
 * Global application state management object
 * @type {Object}
 * @property {Object} clockData - Current clock display data
 * @property {string} clockData.time - Time display value
 * @property {string} clockData.content - Message content from Telegram
 * @property {string|null} clockData.imageData - Base64 encoded image data
 * @property {string} clockData.created_at - ISO timestamp of last update
 * @property {boolean} isConnected - Server connection status
 * @property {Date|null} lastFetchTime - Last successful data fetch time
 * @property {number} retryCount - Current retry attempt counter
 * @property {number} maxRetries - Maximum retry attempts allowed
 */
const appState = {
    clockData: {
        time: "23:56:55",
        content: "",
        imageData: null,
        created_at: new Date().toISOString()
    },
    isConnected: false,
    lastFetchTime: null,
    retryCount: 0,
    maxRetries: 3
};

/**
 * Split Telegram message into header and body, with HTML markup for the body
 * @param {string} content - Raw Telegram message content
 * @returns {{ headerHtml: string, bodyHtml: string }} Formatted parts
 */
function formatTelegramMessage(content) {
    console.log('Formatting Telegram message:', content);

    if (!content) return { headerHtml: '', bodyHtml: '' };

    let headerHtml = '';
    let body = content || '';

    // Remove bold asterisks before time if present
    body = body.replace(/^\*\*(\d{2}:\d{2}:\d{2})/m, '$1');

    // Extract leading time header line if present
    const headerMatch = body.match(/^(\d{2}:\d{2}:\d{2}\s+\([^)]+\)\s*\|\s*\d+\s+секунд[ау]?\s+\([^)]+\))\n\n/m);
    if (headerMatch) {
        headerHtml = `<strong>${headerMatch[1]}</strong>`;
        body = body.replace(headerMatch[0], '');
    }

    // Remove trailing promo block(s) and collect links for left pane
    const promo = extractPromoLinks(body);
    body = promo.cleaned;

    // Emulate simple Markdown formatting in the body
    body = body.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    body = body.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em>$1</em>');
    body = body.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Emoji indicators
    body = body.replace(/🟡/g, '<span class="emoji-indicator yellow">🟡</span>');
    body = body.replace(/🟢/g, '<span class="emoji-indicator green">🟢</span>');
    body = body.replace(/🔴/g, '<span class="emoji-indicator red">🔴</span>');

    // Line breaks
    body = body.replace(/\n/g, '<br>');

    // Cleanup duplicated header markers
    body = body.replace(/\*\*<br>Другие новости/g, '<br>Другие новости');

    const result = { headerHtml, bodyHtml: body, promoHtml: promo.html };
    console.log('Formatted message parts:', result);
    return result;
}

/**
 * Extract trailing promo lines from raw text and return cleaned text + promo HTML
 * Handles two known variants of the footer content.
 * @param {string} text
 * @returns {{ cleaned: string, html: string }}
 */
function extractPromoLinks(text) {
    let cleaned = text.trimEnd();
    let html = '';

    // Variant B: three sentences with parenthetical URLs
    const reThree = /Свежий\s+договорняковый\s+дайджест\.\s*\((https?:\/\/[^\s)]+)\)\s*Поддержать\s+проект\.\s*\((https?:\/\/[^\s)]+)\)\s*Часы\s+судного\s+договорняка\.\s*\((https?:\/\/[^\s)]+)\)\s*$/ims;
    const mThree = cleaned.match(reThree);
    if (mThree) {
        cleaned = cleaned.replace(reThree, '').trimEnd();
        const [_, digestUrl, supportUrl, clockUrl] = mThree;
        html = [
            `<div><a href="${digestUrl}" target="_blank" rel="noopener">Свежий договорняковый дайджест</a>.</div>`,
            `<div><a href="${supportUrl}" target="_blank" rel="noopener">Поддержать проект</a>.</div>`,
            `<div><a href="${clockUrl}" target="_blank" rel="noopener">Часы судного договорняка</a>.</div>`
        ].join('');
        return { cleaned, html };
    }

    // Variant A: single line about digest
    const reDigest = /Другие\s+новости\s+за\s+последние\s+дни\s+читайте\s+в\s+нашем\s+дайджесте\s*\((https?:\/\/[^\s)]+)\)\.?\s*$/ims;
    const mDigest = cleaned.match(reDigest);
    if (mDigest) {
        cleaned = cleaned.replace(reDigest, '').trimEnd();
        const digestUrl = mDigest[1];
        html = `<div><a href="${digestUrl}" target="_blank" rel="noopener">Другие новости за последние дни — дайджест</a></div>`;
    }

    return { cleaned, html };
}

/**
 * Update the clock display with current data from appState
 * Updates both text content and image display
 */
function updateClock() {
    console.log('Updating display with data:', {
        hasImage: !!appState.clockData.imageData,
        hasContent: !!appState.clockData.content
    });
    
    const messageText = document.getElementById('messageText');
    const timeHeader = document.getElementById('timeHeader');
    const promoLinks = document.getElementById('promoLinks');
    if (messageText && timeHeader) {
        if (appState.clockData.content) {
            const { headerHtml, bodyHtml, promoHtml } = formatTelegramMessage(appState.clockData.content);
            timeHeader.innerHTML = headerHtml;
            messageText.innerHTML = bodyHtml || '';
            if (promoLinks) promoLinks.innerHTML = promoHtml || '';
        } else {
            timeHeader.innerHTML = '';
            messageText.textContent = appState.isConnected ?
                'Сообщение не найдено' :
                'Нет подключения к серверу';
            if (promoLinks) promoLinks.innerHTML = '';
        }
    }
    
    const clockImage = document.getElementById('clockImage');
    const noImageMessage = document.getElementById('noImageMessage');
    
    if (appState.clockData.imageData) {
        clockImage.src = `data:image/jpeg;base64,${appState.clockData.imageData}`;
        clockImage.style.display = 'block';
        noImageMessage.style.display = 'none';
        console.log('Displayed image from Telegram');
    } else {
        clockImage.style.display = 'none';
        noImageMessage.style.display = 'block';
        noImageMessage.textContent = appState.isConnected ? 
            'Изображение не найдено в сообщении' : 
            'Нет подключения к серверу';
    }
    
    const contentLayout = document.querySelector('.content-layout');
    if (contentLayout) {
        contentLayout.style.opacity = appState.isConnected ? '1' : '0.7';
    }
}

/**
 * Fetch latest clock data from the API server
 * @returns {Promise<Object>} Clock data response from server
 * @throws {Error} If network request fails or server returns error
 */
async function fetchClockData() {
    try {
        console.log('Загрузка данных с сервера...');
        
        const response = await fetch(`${API_BASE_URL}/clock/latest`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            signal: AbortSignal.timeout(10000)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        appState.clockData.time = data.time || "23:56";
        appState.clockData.content = data.content || "";
        appState.clockData.imageData = data.image_data;
        appState.clockData.created_at = data.created_at;
        
        console.log('Updated app state:', appState.clockData);
        
        appState.isConnected = true;
        appState.lastFetchTime = new Date();
        appState.retryCount = 0;
        
        console.log('Данные обновлены:', data);
        updateClock();
        
        return data;
        
    } catch (error) {
        console.error('Ошибка загрузки данных:', error);
        appState.isConnected = false;
        appState.retryCount++;
        
        updateClock();
        throw error;
    }
}

/**
 * Check server health status
 * @returns {Promise<Object|null>} Server status object or null if unreachable
 */
async function checkServerStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            method: 'GET',
            signal: AbortSignal.timeout(5000)
        });
        
        if (response.ok) {
            const status = await response.json();
            console.log('Статус сервера:', status);
            return status;
        }
    } catch (error) {
        console.error('Ошибка проверки статуса:', error);
    }
    
    return null;
}

/**
 * Auto-update function with retry logic
 * Attempts to fetch new data with exponential backoff on failure
 */
async function autoUpdate() {
    try {
        await fetchClockData();
    } catch (error) {
        if (appState.retryCount < appState.maxRetries) {
            console.log(`Повторная попытка ${appState.retryCount}/${appState.maxRetries} через 5 секунд...`);
            setTimeout(autoUpdate, 5000);
        } else {
            console.error('Превышено максимальное количество попыток подключения');
        }
    }
}

/**
 * Application initialization on DOM content loaded
 * Sets up initial display, checks server status, and starts update intervals
 */
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Инициализация приложения...');
    
    updateClock();
    
    const serverStatus = await checkServerStatus();
    if (serverStatus) {
        console.log('Сервер доступен, загружаем данные...');
        await autoUpdate();
        
        setInterval(autoUpdate, 120000);
        
        setInterval(checkServerStatus, 30000);
    } else {
        console.warn('Сервер недоступен, работаем в оффлайн режиме');
    }

    // No explicit resize handler needed: flex layout sizes the scroll area automatically
});

// Export functions to global window object for debugging and external access
window.fetchClockData = fetchClockData;
window.checkServerStatus = checkServerStatus;
window.updateClock = updateClock;
