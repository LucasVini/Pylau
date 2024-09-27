import os
import paramiko
import socket
import time
import argparse
import logging  # Importar o módulo logging

# Diretório onde os arquivos recebidos serão armazenados
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECEIVED_DIR = os.path.join(BASE_DIR, 'SFTP_RECEBIDO')

# Cria o diretório para os arquivos recebidos se não existir
if not os.path.exists(RECEIVED_DIR):
    os.makedirs(RECEIVED_DIR)

class StubServer(paramiko.ServerInterface):
    def check_auth_password(self, username, password):
        return paramiko.AUTH_SUCCESSFUL

    def check_auth_publickey(self, username, key):
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED

    def get_allowed_auths(self, username):
        return "password,publickey"

class StubSFTPHandle(paramiko.SFTPHandle):
    def stat(self):
        try:
            return paramiko.SFTPAttributes.from_stat(os.fstat(self.readfile.fileno()))
        except OSError as e:
            return paramiko.SFTPServer.convert_errno(e.errno)

    def chattr(self, attr):
        try:
            paramiko.SFTPServer.set_file_attr(self.filename, attr)
            return paramiko.SFTP_OK
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

def start_server(host, port, keyfile, level):
    # Configurar o logging diretamente usando o módulo logging
    logging.basicConfig(level=getattr(logging, level.upper(), logging.INFO))

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
    server_socket.bind((host, port))
    server_socket.listen(10)

    print(f'Servidor SFTP rodando em {host}:{port}')

    while True:
        conn, addr = server_socket.accept()

        host_key = paramiko.RSAKey.generate(2048)  # Gerar chave RSA
        transport = paramiko.Transport(conn)
        transport.add_server_key(host_key)
        transport.set_subsystem_handler('sftp', paramiko.SFTPServer, StubSFTPServer)

        server = StubServer()
        transport.start_server(server=server)

        channel = transport.accept()
        if channel is None:
            print("Falha na autenticação.")
        else:
            print("Cliente conectado.")

        while transport.is_active():
            time.sleep(1)

def principal():
    parser = argparse.ArgumentParser(description='Start a simple SFTP server.')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=3373, help='Port to bind (default: 3373)')
    parser.add_argument('--level', default='INFO', help='Logging level (default: INFO)')
    parser.add_argument('--keyfile', required=False, help='Path to private key file')

    args = parser.parse_args()

    if args.keyfile:
        start_server(args.host, args.port, args.keyfile, args.level)
    else:
        start_server(args.host, args.port, None, args.level)

if __name__ == '__main__':
    principal()