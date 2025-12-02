// Service Worker for Push Notifications
const CACHE_NAME = 'flask-push-v1';

self.addEventListener('install', function(event) {
    console.log('Service Worker installing...');
    // Активировать сразу без ожидания
    self.skipWaiting();
});

self.addEventListener('activate', function(event) {
    console.log('Service Worker activating...');
    // Взять контроль над всеми клиентами сразу
    event.waitUntil(self.clients.claim());
});

self.addEventListener('push', function(event) {
    console.log('Push event received');
    
    let data = {};
    try {
        data = event.data.json();
    } catch (e) {
        data = {
            title: 'Flask App',
            body: 'New notification',
            icon: '/static/icon-192x192.png'
        };
    }
    
    const options = {
        body: data.body || 'Notification body',
        icon: data.icon || '/static/icon-192x192.png',
        badge: '/static/badge-72x72.png',
        tag: data.tag || 'flask-app'
    };
    
    event.waitUntil(
        self.registration.showNotification(
            data.title || 'Flask App Notification',
            options
        )
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    
    event.waitUntil(
        clients.matchAll({type: 'window'}).then(function(clientList) {
            for (let client of clientList) {
                if (client.url === '/' && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow('/');
            }
        })
    );
});