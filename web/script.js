// Конфигурация API
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api' 
    : '/api';

// Состояние приложения
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

function formatTelegramMessage(content) {
    console.log('Formatting Telegram message:', content);
    
    if (!content) return '';
    
    let formatted = content;
    
    // Убираем лишние звездочки в начале сообщения (например, **23:56:05)
    formatted = formatted.replace(/^\*\*(\d{2}:\d{2}:\d{2})/m, '$1');
    
    // Выделяем время в начале сообщения как жирное и убираем лишние переносы
    formatted = formatted.replace(/^(\d{2}:\d{2}:\d{2}\s+\([^)]+\)\s*\|\s*\d+\s+секунд[ау]?\s+\([^)]+\))\n\n/m, 
        '<div class="time-header"><strong>$1</strong></div>');
    
    // Преобразуем жирный текст **текст** в <strong>текст</strong>
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Преобразуем курсив *текст* в <em>текст</em> (но не затрагиваем уже обработанные **)
    formatted = formatted.replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em>$1</em>');
    
    // Преобразуем ссылки [текст](url) в <a href="url">текст</a>
    formatted = formatted.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    
    // Преобразуем эмодзи-индикаторы в цветные блоки
    formatted = formatted.replace(/🟡/g, '<span class="emoji-indicator yellow">🟡</span>');
    formatted = formatted.replace(/🟢/g, '<span class="emoji-indicator green">🟢</span>');
    formatted = formatted.replace(/🔴/g, '<span class="emoji-indicator red">🔴</span>');
    
    // Добавляем разрывы строк
    formatted = formatted.replace(/\n/g, '<br>');
    
    // Убираем лишние звездочки в конце перед "Другие новости"
    formatted = formatted.replace(/\*\*<br>Другие новости/g, '<br>Другие новости');
    
    console.log('Formatted message:', formatted);
    return formatted;
}

function updateClock() {
    console.log('Updating display with data:', {
        hasImage: !!appState.clockData.imageData,
        hasContent: !!appState.clockData.content
    });
    
    // Обновляем текст сообщения с форматированием
    const messageContent = document.getElementById('messageContent');
    if (messageContent) {
        if (appState.clockData.content) {
            messageContent.innerHTML = formatTelegramMessage(appState.clockData.content);
        } else {
            messageContent.textContent = appState.isConnected ? 
                'Сообщение не найдено' : 
                'Нет подключения к серверу';
        }
    }
    
    // Обновляем изображение
    const clockImage = document.getElementById('clockImage');
    const noImageMessage = document.getElementById('noImageMessage');
    
    if (appState.clockData.imageData) {
        // Показываем изображение из Telegram канала
        clockImage.src = `data:image/jpeg;base64,${appState.clockData.imageData}`;
        clockImage.style.display = 'block';
        noImageMessage.style.display = 'none';
        console.log('Displayed image from Telegram');
    } else {
        // Скрываем изображение и показываем сообщение
        clockImage.style.display = 'none';
        noImageMessage.style.display = 'block';
        noImageMessage.textContent = appState.isConnected ? 
            'Изображение не найдено в сообщении' : 
            'Нет подключения к серверу';
    }
    
    // Индикатор подключения через прозрачность контейнера
    const contentLayout = document.querySelector('.content-layout');
    if (contentLayout) {
        contentLayout.style.opacity = appState.isConnected ? '1' : '0.7';
    }
}

// Функция загрузки данных с сервера
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
        
        // Обновляем состояние приложения новыми данными
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

// Функция проверки статуса сервера
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

// Функция автоматического обновления с повторными попытками
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

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', async function() {
    console.log('Инициализация приложения...');
    
    // Показываем дефолтные данные сразу
    updateClock();
    
    // Проверяем статус сервера
    const serverStatus = await checkServerStatus();
    if (serverStatus) {
        console.log('Сервер доступен, загружаем данные...');
        // Загружаем актуальные данные
        await autoUpdate();
        
        // Настраиваем автообновление каждые 2 минуты
        setInterval(autoUpdate, 120000);
        
        // Дополнительная проверка статуса каждые 30 секунд
        setInterval(checkServerStatus, 30000);
    } else {
        console.warn('Сервер недоступен, работаем в оффлайн режиме');
    }
});

// Экспортируем функции для использования в консоли
window.fetchClockData = fetchClockData;
window.checkServerStatus = checkServerStatus;
window.updateClock = updateClock;