// Скрипт для предзагрузки всех фото при загрузке страницы
(function() {
    console.log('🚀 Preload script started');

    // Функция для загрузки с отключенным кэшем
    async function fetchWithNoCache(url) {
        try {
            const response = await fetch(url, {
                cache: 'no-cache',
                headers: {
                    'Cache-Control': 'no-cache, no-store',
                    'Pragma': 'no-cache'
                }
            });
            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${url}:`, error);
            return null;
        }
    }

    // Предзагружаем все API при старте
    async function preloadAll() {
        const apis = ['/api/gallery', '/api/content', '/api/home-images'];

        for (const api of apis) {
            console.log(`📥 Preloading: ${api}`);
            await fetchWithNoCache(api);
        }

        console.log('✅ All APIs preloaded');

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