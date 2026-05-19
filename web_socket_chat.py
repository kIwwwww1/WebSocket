from random import randint

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()


class ConnectionManager:
    def __init__(self) -> None:
        # Список для хранения всех активных WebSocket-сессий
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str) -> None:
        # Отправляем сообщение абсолютно всем подключенным клиентам
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()

html = html = """
<!DOCTYPE html>
<html>
    <head>
        <title>FastAPI WebSocket</title>
    </head>
    <body>
        <h1 id="test-title">WebSocket Тест #</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Отправить</button>
        </form>
        <ul id="messages"></ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            
            ws.onmessage = function(event) {
                if (event.data.startsWith("INITIAL_ID:")) {
                    var testId = event.data.split(":")[1];
                    document.getElementById('test-title').innerText = "WebSocket Тест #" + testId;
                    return; 
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
async def get() -> HTMLResponse:
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    # 1. Регистрируем новое подключение в менеджере
    await manager.connect(websocket)
    TEST_ID = randint(1, 100)

    # Отправляем ID только автору подключения (не через broadcast)
    await websocket.send_text(f"INITIAL_ID:{TEST_ID}")

    # Уведомляем всех, что вошел новый пользователь
    await manager.broadcast(f"Пользователь {TEST_ID} вошел в чат!")

    try:
        while True:
            data = await websocket.receive_text()
            # 2. Рассылаем сообщение ВСЕМ пользователям
            await manager.broadcast(f"{TEST_ID}: {data}")

    except WebSocketDisconnect:
        # 3. Удаляем клиента из списка при отключении
        manager.disconnect(websocket)

        # Уведомляем оставшихся участников
        await manager.broadcast(f"{TEST_ID}: вышел из чата!")
