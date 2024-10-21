import os
import paramiko
import socket
import time
import argparse
import logging
import threading  # Importa o módulo threading

# Função para obter o IP local da máquina
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    except Exception:
        local_ip = "127.0.0.1"
    finally:
        s.close()
    return local_ip

# Diretório onde os arquivos recebidos serão armazenados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIVED_DIR = os.path.join(BASE_DIR, 'SFTP_RECEBIDO')

# Cria o diretório para os arquivos recebidos se não existir
if not os.path.exists(RECEIVED_DIR):
    os.makedirs(RECEIVED_DIR)

class StubServer(paramiko.ServerInterface):
    def check_auth_password(self, username, password):
        # Autenticação de usuário e senha
        if username == "admin" and password == "@1234567":
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_FAILED  # Para desativar autenticação por chave pública

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED

    def get_allowed_auths(self, username):
        return "password"

class StubSFTPHandle(paramiko.SFTPHandle):
    def stat(self):
        try:
            return paramiko.SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

class StubSFTPServer(paramiko.SFTPServerInterface):
    ROOT = RECEIVED_DIR

    def _realpath(self, path):
        return os.path.join(self.ROOT, path.lstrip('/'))

    def list_folder(self, path):
        path = self._realpath(path)
        try:
            out = []
            flist = os.listdir(path)
            for fname in flist:
                attr = paramiko.SFTPAttributes.from_stat(os.stat(os.path.join(path, fname)))
                attr.filename = fname
                out.append(attr)
            return out
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def stat(self, path):
        path = self._realpath(path)
        try:
            return paramiko.SFTPAttributes.from_stat(os.stat(path))
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def lstat(self, path):
        path = self._realpath(path)
        try:
            return paramiko.SFTPAttributes.from_stat(os.lstat(path))
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def open(self, path, flags, attr):
        path = self._realpath(path)
        try:
            binary_flag = getattr(os, 'O_BINARY', 0)
            flags |= binary_flag
            mode = getattr(attr, 'st_mode', None)
            if mode is not None:
                fd = os.open(path, flags, mode)
            else:
                fd = os.open(path, flags, 0o666)
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)
        if (flags & os.O_CREAT) and (attr is not None):
            attr._flags &= ~attr.FLAG_PERMISSIONS
            paramiko.SFTPServer.set_file_attr(path, attr)
        if flags & os.O_WRONLY:
            if flags & os.O_APPEND:
                fstr = 'ab'
            else:
                fstr = 'wb'
        elif flags & os.O_RDWR:
            if flags & os.O_APPEND:
                fstr = 'a+b'
            else:
                fstr = 'r+b'
        else:
            fstr = 'rb'
        try:
            f = os.fdopen(fd, fstr)
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)
        fobj = StubSFTPHandle(flags)
        fobj.filename = path
        fobj.readfile = f
        fobj.writefile = f
        return fobj

    def remove(self, path):
        path = self._realpath(path)
        try:
            os.remove(path)
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)
        return paramiko.SFTP_OK

    def rename(self, oldpath, newpath):
        oldpath = self._realpath(oldpath)
        newpath = self._realpath(newpath)
        try:
            os.rename(oldpath, newpath)
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)
        return paramiko.SFTP_OK

    def mkdir(self, path, attr):
        path = self._realpath(path)
        try:
            os.mkdir(path)
            if attr is not None:
                paramiko.SFTPServer.set_file_attr(path, attr)
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)
        return paramiko.SFTP_OK

    def rmdir(self, path):
        path = self._realpath(path)
        try:
            os.rmdir(path)
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)
        return paramiko.SFTP_OK

    def chattr(self, path, attr):
        path = self._realpath(path)
        try:
            paramiko.SFTPServer.set_file_attr(path, attr)
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)
        return paramiko.SFTP_OK

    def symlink(self, target_path, path):
        path = self._realpath(path)
        if (len(target_path) > 0) and (target_path[0] == '/'):
            target_path = os.path.join(self.ROOT, target_path[1:])
        else:
            abspath = os.path.join(os.path.dirname(path), target_path)
            if abspath[:len(self.ROOT)] != self.ROOT:
                target_path = '<error>'
        try:
            os.symlink(target_path, path)
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)
        return paramiko.SFTP_OK

    def readlink(self, path):
        path = self._realpath(path)
        try:
            symlink = os.readlink(path)
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)
        if os.path.isabs(symlink):
            if symlink[:len(self.ROOT)] == self.ROOT:
                symlink = symlink[len(self.ROOT):]
                if (len(symlink) == 0) or (symlink[0] != '/'):
                    symlink = '/' + symlink
            else:
                symlink = '<error>'
        return symlink

class SFTPServerThread(threading.Thread):
    def __init__(self, host, port, keyfile, level):
        super().__init__()
        self.host = host
        self.port = port
        self.keyfile = keyfile
        self.level = level
        self.running = True  # Flag para controlar a execução da thread

    def run(self):
        logging.basicConfig(level=getattr(logging, self.level.upper(), logging.INFO))

        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        server_socket.bind((self.host, self.port))
        server_socket.listen(10)

        local_ip = get_local_ip()
        print(f'Servidor SFTP rodando em {local_ip}:{self.port}')

        while self.running:
            try:
                conn, addr = server_socket.accept()

                host_key = paramiko.RSAKey.generate(2048)
                transport = paramiko.Transport(conn)
                transport.add_server_key(host_key)
                transport.set_subsystem_handler('sftp', paramiko.SFTPServer, StubSFTPServer)

                server = StubServer()
                try:
                    transport.start_server(server=server)
                except paramiko.SSHException as e:
                    print(f"Erro de autenticação: {e}")
                    continue  # Ignora o erro e continua aguardando novas conexões

                channel = transport.accept()
                if channel is None:
                    print("Falha na autenticação.")
                else:
                    print("Cliente conectado.")

                while transport.is_active():
                    time.sleep(1)

            except Exception as e:
                print(f"Erro no servidor: {e}")

        # Fecha o socket do servidor ao parar
        server_socket.close()

    def stop(self):
        self.running = False  # Para a execução da thread

def start_server(host, port, keyfile, level):
    server_thread = SFTPServerThread(host, port, keyfile, level)
    server_thread.start()
    return server_thread

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='0.0.0.0', help='Host para escutar (padrão: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=2222, help='Porta para escutar (padrão: 2222)')
    parser.add_argument('--keyfile', default='test_rsa.key', help='Arquivo de chave privada (padrão: test_rsa.key)')
    parser.add_argument('--loglevel', default='info', help='Nível de log (padrão: info)')
    args = parser.parse_args()

    server_thread = start_server(args.host, args.port, args.keyfile, args.loglevel)

    # Mantém o programa principal em execução
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Parando o servidor...")
        server_thread.stop()

if __name__ == '__main__':
    main()
