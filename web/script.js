// Конфигурация API
const API_BASE_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8000/api' 
    : '/api';

// Состояние приложения
const appState = {
    clockData: {
        time: "23:56:55",
        minutes: 2,
        seconds: 40,
        date: "20 августа 2025 года, 1274 день",
        currentTime: "23:57:20 (-5) | 160 секунд (+5)",
        lastUpdate: new Date().toISOString()
    },
    isConnected: false,
    lastFetchTime: null,
    retryCount: 0,
    maxRetries: 3
};

function parseTimeString(timeStr) {
    // Парсим время в формате "23:56" или "23:56:55" 
    const parts = timeStr.split(':');
    if (parts.length >= 2) {
        const hours = parseInt(parts[0]);
        const minutes = parseInt(parts[1]);
        const seconds = parts.length > 2 ? parseInt(parts[2]) : 0;
        
        // Вычисляем ОСТАВШЕЕСЯ время до полуночи (24:00)
        // Если сейчас 23:56:00, то до полуночи осталось 4 минуты 0 секунд
        let finalMinutes, finalSeconds;
        
        if (seconds === 0) {
            finalMinutes = 60 - minutes;
            finalSeconds = 0;
        } else {
            finalMinutes = 60 - minutes - 1;
            finalSeconds = 60 - seconds;
        }
        
        // Если часы не 23, то считаем полное время до полуночи
        if (hours < 23) {
            // Всего секунд до полуночи (24:00:00)
            const totalSecondsLeft = (24 - hours) * 3600 - (minutes * 60) - seconds;
            finalMinutes = Math.floor(totalSecondsLeft / 60);
            finalSeconds = totalSecondsLeft % 60;
        }
        
        return {
            displayMinutes: finalMinutes,
            displaySeconds: finalSeconds,
            hourAngle: (hours % 12) * 30 + (minutes * 0.5), // 30 градусов за час + смещение от минут
            minuteAngle: minutes * 6 // 6 градусов за минуту (360/60)
        };
    }
    return { displayMinutes: 4, displaySeconds: 0, hourAngle: 345, minuteAngle: 336 };
}

function updateClock() {
    console.log('Updating clock with time:', appState.clockData.time);
    const parsed = parseTimeString(appState.clockData.time);
    console.log('Parsed time:', parsed);
    
    // Обновляем большие цифры
    const minutesEl = document.getElementById('minutes');
    const secondsEl = document.getElementById('seconds');
    
    if (minutesEl) {
        minutesEl.textContent = parsed.displayMinutes;
        console.log('Set minutes to:', parsed.displayMinutes);
    }
    if (secondsEl) {
        secondsEl.textContent = parsed.displaySeconds.toString().padStart(2, '0');
        console.log('Set seconds to:', parsed.displaySeconds);
    }
    
    // Обновляем стрелки часов
    const minuteHand = document.getElementById('minuteHand');
    const hourHand = document.getElementById('hourHand');
    
    if (minuteHand && hourHand) {
        minuteHand.style.transform = `translate(-50%, -100%) rotate(${parsed.minuteAngle}deg)`;
        hourHand.style.transform = `translate(-50%, -100%) rotate(${parsed.hourAngle}deg)`;
    }
    
    // Обновляем дату и время
    const dateEl = document.getElementById('dateText');
    const currentTimeEl = document.getElementById('currentTime');
    
    if (dateEl) dateEl.textContent = appState.clockData.date;
    if (currentTimeEl) currentTimeEl.textContent = appState.clockData.currentTime;
    
    // Индикатор подключения
    if (minutesEl && secondsEl) {
        const opacity = appState.isConnected ? '1' : '0.7';
        minutesEl.style.opacity = opacity;
        secondsEl.style.opacity = opacity;
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
        
        // Обновляем состояние приложения
        let extractedTime = data.time || "23:56";
        
        // Парсим контент для извлечения ПОЛНОГО времени с секундами
        if (data.content) {
            console.log('Parsing content:', data.content);
            
            // Ищем ТОЧНОЕ время в формате "23:56:00" в начале сообщения
            const fullTimeMatch = data.content.match(/\*?\*?(\d{1,2}):(\d{2}):(\d{2})/);
            if (fullTimeMatch) {
                const hours = fullTimeMatch[1].padStart(2, '0');
                const minutes = fullTimeMatch[2];
                const seconds = fullTimeMatch[3];
                extractedTime = `${hours}:${minutes}:${seconds}`;
                console.log('Extracted FULL time from content:', extractedTime);
            }
            
            // Ищем дату в формате "20 августа 2025 года, 1274 день"
            const dateMatch = data.content.match(/(\d{1,2}\s+\w+\s+\d{4}\s+года,\s+\d+\s+день)/);
            if (dateMatch) {
                appState.clockData.date = dateMatch[1];
            }
            
            // Ищем время с изменениями в формате "23:57:20 (-5) | 160 секунд (+5)"
            const timeMatch = data.content.match(/(\d{2}:\d{2}:\d{2}\s+\([^)]+\)\s+\|\s+\d+\s+секунд\s+\([^)]+\))/);
            if (timeMatch) {
                appState.clockData.currentTime = timeMatch[1];
            }
        }
        
        appState.clockData.time = extractedTime;
        appState.clockData.lastUpdate = data.created_at;
        
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