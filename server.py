import asyncio
import datetime
from asyncio import transports


def get_time():
    return datetime.datetime.now().strftime("%d-%m-%Y %H:%M")


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
                if login.lower() not in self.server.login_list:
                    self.login = login
                    self.transport.write('Успешная регистрация\r\n'.encode())
                    self.server.login_list.append(self.login.lower())
                    self.send_history()
                    print(f'({get_time()}) User {self.login} register')
                else:
                    self.transport.write(f'Логин {login} уже существует! Выберите другой\r\n'.encode())
            else:
                self.transport.write('Вы не авторизованы, напишите "login:"\r\n'.encode())

    def send_message(self, content):
        message = f'{self.login}: {content}\r\n'.encode()
        self.server.message_list.append(message.decode())

        for user in self.server.clients:
            user.transport.write(message)

    def send_history(self):
        last_message = 11
        if len(self.server.message_list) < 10:
            last_message = len(self.server.message_list)+1
        self.transport.write('=======================\r\n'.encode())
        for message in reversed(self.server.message_list[-1:-last_message:-1]):
            self.transport.write(f'{message}'.encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport

        print(f'({get_time()}) User connection')

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        self.server.login_list.remove(self.login)
        print(f'({get_time()}) User {self.login} disconnection')


class Server:
    clients: list
    login_list: list
    message_list: list

    def __init__(self):
        self.clients = []
        self.login_list = []
        self.message_list = []

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
