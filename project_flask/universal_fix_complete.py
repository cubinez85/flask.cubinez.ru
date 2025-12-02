import os
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend

def universal_fix_complete():
    print("🎯 УНИВЕРСАЛЬНОЕ исправление для pywebpush (ПОЛНАЯ ВЕРСИЯ)...")
    
    # 1. Генерируем новые ключи
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    
    # 2. Приватный ключ в Base64 для pywebpush
    private_numbers = private_key.private_numbers()
    private_raw = private_numbers.private_value.to_bytes(32, 'big')
    private_b64 = base64.urlsafe_b64encode(private_raw).decode('utf-8').rstrip('=')
    
    # 3. Публичный ключ в Base64 для JavaScript
    public_key = private_key.public_key()
    public_numbers = public_key.public_numbers()
    x = public_numbers.x.to_bytes(32, 'big')
    y = public_numbers.y.to_bytes(32, 'big')
    uncompressed_point = b'\x04' + x + y
    public_b64 = base64.urlsafe_b64encode(uncompressed_point).decode('utf-8').rstrip('=')
    
    # 4. Также публичный ключ в PEM для сервера (если нужно)
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8').strip()
    
    print(f"✅ Сгенерированы ключи:")
    print(f"Приватный (Base64): {private_b64}")
    print(f"Публичный (Base64 для JS): {public_b64}")
    print(f"Публичный (PEM): {public_pem[:50]}...")
    
    # 5. Обновляем .env - добавляем ОБА ключа
    env_path = '/var/www/project_flask/.env'
    
    with open(env_path, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if not line.startswith('VAPID_'):
            new_lines.append(line)
    
    # Добавляем ОБА ключа в Base64 формате
    new_lines.append(f'VAPID_PRIVATE_KEY={private_b64}\n')
    new_lines.append(f'VAPID_PUBLIC_KEY={public_b64}\n')
    
    with open(env_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"\n📝 В .env добавлены ОБА ключа:")
    print(f"VAPID_PRIVATE_KEY={private_b64}")
    print(f"VAPID_PUBLIC_KEY={public_b64}")
    
    print(f"\n🌐 Для base.html:")
    print(f"const VAPID_PUBLIC_KEY = '{public_b64}';")
    
    return private_b64, public_b64

if __name__ == '__main__':
    universal_fix_complete()
