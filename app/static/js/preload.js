// Скрипт для предзагрузки всех API
(function() {
    console.log('🚀 Preload script started');

    async function fetchWithNoCache(url) {
        try {
            // Убеждаемся что URL заканчивается на слеш
            let fixedUrl = url;
            if (!fixedUrl.endsWith('/') && (fixedUrl.includes('/api/') || fixedUrl.includes('/home-images'))) {
                fixedUrl = fixedUrl + '/';
            }

            console.log(`📥 Preloading: ${fixedUrl}`);
            const response = await fetch(fixedUrl, {
                cache: 'no-cache',
                headers: {
                    'Cache-Control': 'no-cache, no-store',
                    'Pragma': 'no-cache'
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log(`✅ Preloaded: ${fixedUrl}`, Array.isArray(data) ? `${data.length} items` : 'OK');
            return data;
        } catch (error) {
            console.error(`Error preloading ${url}:`, error);
            return null;
        }
    }

    async function preloadAll() {
        const apis = [
            '/api/gallery/',
            '/api/content/',
            '/api/home-images/',
            '/api/prices/',
            '/api/comments/approved'
        ];

        for (const api of apis) {
            await fetchWithNoCache(api);
            // Небольшая задержка между запросами
            await new Promise(resolve => setTimeout(resolve, 100));
        }

        console.log('✅ All APIs preloaded successfully');

        // Триггерим событие для страницы
        window.dispatchEvent(new CustomEvent('apiPreloaded'));
    }

    // Запускаем предзагрузку сразу
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', preloadAll);
    } else {
        preloadAll();
    }
})();