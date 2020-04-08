import asyncio
from asyncio import transports

login_list = []
message_list = []


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):

        decoded = data.decode(errors='ignore')

        if self.login is not None:
            if data.decode().replace('\r\n', ''):
                self.send_message(decoded)
        else:
            if decoded.startswith('login:'):
                login = decoded.replace('login:', '').replace("/r/n", "").replace(' ', '')
                if login.lower() not in login_list:
                    self.login = login
                    self.transport.write('Успешная регистрация\r\n'.encode())
                    login_list.append(self.login.lower())
                    self.send_history()
                else:
                    self.transport.write('Логин уже существует! Выберите другой\r\n'.encode())
            else:
                self.transport.write('Вы не авторизованы, напишите "login:"\r\n'.encode())

    def send_message(self, content):
        message = f'{self.login}: {content}\r\n'.encode()
        message_list.append(message.decode())

        for user in self.server.clients:
            user.transport.write(message)

    def send_history(self):
        last_message = 11
        if len(message_list) < 10:
            last_message = len(message_list)
        self.transport.write('=======================\r\n'.encode())
        for message in reversed(message_list[-1:-last_message:-1]):
            self.transport.write(f'{message}'.encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport

        print('User connection')

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print(f'User {self.login} disconnection')


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            'localhost',
            8888
        )

        print('Server started')

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print('Остановлено вручную')
