from flask import jsonify, request, current_app, url_for
from app.api import bp
import json
import logging
from urllib.parse import urlparse
from app.models import User

logger = logging.getLogger(__name__)

@bp.route('/vapidPublicKey', methods=['GET'])
def vapid_public_key_legacy():
    """Старый эндпоинт для совместимости с существующим кодом"""
    public_key = current_app.config.get('VAPID_PUBLIC_KEY')
    if not public_key:
        logger.error("VAPID public key not configured")
        return 'VAPID key not configured', 500

    logger.info("VAPID public key requested via legacy endpoint")
    return public_key

@bp.route('/push/vapid_public_key', methods=['GET'])
def get_vapid_public_key():
    """Новый эндпоинт возвращает JSON"""
    public_key = current_app.config.get('VAPID_PUBLIC_KEY')
    if not public_key:
        return jsonify({'error': 'VAPID public key not configured'}), 500

    return jsonify({
        'publicKey': public_key
    })

@bp.route('/push/test', methods=['POST'])
def push_test():
    """Тестовый эндпоинт для отправки push-уведомлений"""
    try:
        from pywebpush import webpush, WebPushException

        subscription_info = request.json
        if not subscription_info:
            return jsonify({'error': 'No subscription provided'}), 400

        # Проверяем наличие ключей
        vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
        vapid_public_key = current_app.config.get('VAPID_PUBLIC_KEY')

        if not vapid_private_key or not vapid_public_key:
            return jsonify({'error': 'VAPID keys not configured'}), 500

        # Формируем сообщение
        message = {
            'title': '✅ Test Notification',
            'body': 'This is a test push notification from Flask!',
            'icon': '/static/icon-192x192.png',
            'badge': '/static/badge-72x72.png',
            'url': '/'
        }

        # VAPID claims
        vapid_claims = {
            "sub": "mailto:admin@flask.cubinez.ru",
            "aud": get_audience(subscription_info.get('endpoint'))
        }

        # Отправляем push
        webpush(
            subscription_info=subscription_info,
            data=json.dumps(message),
            vapid_private_key=vapid_private_key,
            vapid_claims=vapid_claims
        )

        logger.info("Push notification sent successfully")
        return jsonify({'status': 'success', 'message': 'Push sent successfully'})

    except ImportError:
        logger.error("pywebpush not installed")
        return jsonify({'error': 'Push notifications not available'}), 500
    except Exception as e:
        logger.error(f'Push error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@bp.route('/push/subscribe', methods=['POST'])
def push_subscribe():
    """Сохраняет подписку пользователя"""
    try:
        from flask_login import current_user
        
        if current_user.is_anonymous:
            return jsonify({'error': 'Not authenticated'}), 401

        subscription = request.json
        if not subscription:
            return jsonify({'error': 'No subscription provided'}), 400

        # Сохраняем подписку в базу данных пользователя
        current_user.push_subscription = json.dumps(subscription)
        from app import db
        db.session.commit()

        endpoint_short = subscription.get('endpoint', '')[:50] + '...' if subscription.get('endpoint') else 'no endpoint'
        logger.info(f"New subscription received for {current_user.username}: {endpoint_short}")

        return jsonify({'status': 'success', 'message': 'Subscription received'})

    except Exception as e:
        logger.error(f'Subscription error: {str(e)}')
        return jsonify({'error': str(e)}), 500

@bp.route('/push/refresh', methods=['POST'])
def push_refresh():
    """Обновляет подписку"""
    try:
        from flask_login import current_user
        from app import db
        
        if current_user.is_anonymous:
            return jsonify({'error': 'Not authenticated'}), 401

        logger.info(f"Push refresh requested for user: {current_user.username}")

        # Очищаем подписку
        current_user.push_subscription = None
        db.session.commit()

        return jsonify({
            'status': 'success', 
            'message': 'Push subscription refreshed. Please create a new subscription.'
        })
    except Exception as e:
        logger.error(f'Refresh error: {str(e)}')
        return jsonify({'error': str(e)}), 500

def send_push_notification(user, title, body, url='/'):
    """Отправляет push-уведомление пользователю"""
    if not user.push_subscription:
        logger.info(f"No push subscription for user {user.username}")
        return False
    
    try:
        from pywebpush import webpush
        
        subscription = json.loads(user.push_subscription)
        
        message = {
            'title': title,
            'body': body,
            'icon': '/static/icon-192x192.png',
            'badge': '/static/badge-72x72.png',
            'url': url
        }
        
        vapid_claims = {
            "sub": "mailto:admin@flask.cubinez.ru",
            "aud": get_audience(subscription.get('endpoint'))
        }
        
        webpush(
            subscription_info=subscription,
            data=json.dumps(message),
            vapid_private_key=current_app.config['VAPID_PRIVATE_KEY'],
            vapid_claims=vapid_claims
        )
        
        logger.info(f"Push notification sent to {user.username}: {title}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send push to {user.username}: {e}")
        # Если подписка невалидна, очищаем ее
        if "expired" in str(e).lower() or "invalid" in str(e).lower():
            user.push_subscription = None
            from app import db
            db.session.commit()
            logger.info(f"Cleared invalid subscription for {user.username}")
        return False

def notify_new_message(recipient, sender, message):
    """Уведомление о новом сообщении"""
    send_push_notification(
        user=recipient,
        title=f"💌 Новое сообщение от {sender.username}",
        body=message.body[:100],
        url=url_for('main.messages', _external=False)
    )

def notify_mention(user, post):
    """Уведомление об упоминании в посте"""
    send_push_notification(
        user=user,
        title="👥 Вас упомянули",
        body=post.body[:100],
        url=url_for('main.post', post_id=post.id, _external=False)
    )

def notify_new_follower(user, follower):
    """Уведомление о новом подписчике"""
    send_push_notification(
        user=user,
        title="➕ Новый подписчик",
        body=f"{follower.username} подписался на вас",
        url=url_for('main.user', username=follower.username, _external=False)
    )

def notify_new_post(user, author, post):
    """Уведомление о новом посте от подписанного автора"""
    send_push_notification(
        user=user,
        title=f"📝 Новый пост от {author.username}",
        body=post.body[:100],
        url=url_for('main.post', post_id=post.id, _external=False)
    )

def get_audience(endpoint):
    """Извлекает audience из endpoint"""
    if not endpoint:
        return "https://fcm.googleapis.com"

    try:
        parsed = urlparse(endpoint)
        return f"{parsed.scheme}://{parsed.netloc}"
    except:
        return "https://fcm.googleapis.com"
