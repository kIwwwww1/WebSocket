from random import randint

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI WebSocket</title>
    </head>
    <body>
        <!-- Добавляем id="test-title", чтобы JavaScript мог найти этот элемент -->
        <h1 id="test-title">WebSocket Тест #</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Отправить</button>
        </form>
        <ul id="messages"></ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            
            ws.onmessage = function(event) {
                // Проверяем, не пришел ли нам TEST_ID при первом подключении
                if (event.data.startsWith("INITIAL_ID:")) {
                    var testId = event.data.split(":")[1];
                    // Меняем текст заголовка h1
                    document.getElementById('test-title').innerText = "WebSocket Тест #" + testId;
                    return; // Выходим из функции, чтобы не выводить это системное сообщение в список
                }

                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                var content = document.createTextNode(event.data);
                message.appendChild(content);
                messages.appendChild(message);
            };
            
            function sendMessage(event) {
                var input = document.getElementById('messageText');
                ws.send(input.value);
                input.value = '';
                event.preventDefault();
            }
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    # 1. Принимаем подключение клиента
    await websocket.accept()
    TEST_ID = randint(1, 100)

    # Сразу после подключения отправляем клиенту его ID со специальным префиксом
    await websocket.send_text(f"INITIAL_ID:{TEST_ID}")

    try:
        while True:
            # 2. Ожидаем текстовое сообщение от клиента
            data = await websocket.receive_text()

            # 3. Отправляем ответ обратно клиенту (эхо-сервер)
            await websocket.send_text(f"#{TEST_ID} отправил сообщение: {data}")

    except WebSocketDisconnect:
        # 4. Обрабатываем отключение клиента
        print(f"{TEST_ID} вышел из чата")
