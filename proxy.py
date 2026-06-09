from flask import Flask, request, Response
import requests

app = Flask(__name__)

# URL вашего основного заблокированного сервера (вне РФ)
TARGET_SERVER = "http://ваш-заблокированный-айпи-или-домен:5000"

# Если на самом сервере в РФ настроен split-tunneling / системный VPN, 
# то requests сам пойдет через нужный маршрут.
# Если нужно пустить трафик через конкретный локальный прокси (например, SOCKS5), раскомментируйте:
PROXIES = {
    # "http": "socks5://127.0.0.1:1080",
    # "https": "socks5://127.0.0.1:1080"
}

@app.after_request
def allow_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS, PUT, DELETE"
    return response

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def proxy(path):
    if request.method == 'OPTIONS':
        return '', 200

    url = f"{TARGET_SERVER}/{path}"
    
    # Копируем заголовки запроса, исключая Host, чтобы не сломать маршрутизацию веб-сервера
    headers = {key: value for key, value in request.headers if key.lower() != 'host'}
    
    try:
        # Отправляем запрос на заблокированный сервер
        response = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=request.get_data(),
            params=request.args,
            proxies=PROXIES if PROXIES else None,
            timeout=15
        )
        
        # Удаляем заголовки, которые могут вызвать конфликты при повторной отправке
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        reply_headers = [(name, value) for name, value in response.raw.headers.items()
                         if name.lower() not in excluded_headers]
        
        return Response(response.content, response.status_code, reply_headers)
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Ошибка соединения с основным сервером: {str(e)}"}, 502

if __name__ == '__main__':
    # Запускаем на порту 5001 (или любом удобном), чтобы не конфликтовать со старым портом
    app.run(host='0.0.0.0', port=5001)
