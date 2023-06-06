import logging
import stat
from abc import ABC, abstractmethod
from ftplib import FTP
from pathlib import Path
from typing import Iterator, List

from paramiko import Transport  # type: ignore
from paramiko.sftp_client import SFTPClient  # type: ignore

logger = logging.getLogger(__name__)


class Connector(ABC):
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnects silently from a concrete connector."""

    @abstractmethod
    def list_files(self, location: str) -> List[str]:
        """Lists items on a remote server in a specified directory of a
        concrete connector."""

    def save_file(self, filename: str, location: str) -> None:
        """Saves a file from a remote server to a provided location on a local
        machine of a concrete connector."""


class FTPConnector(Connector):
    def __init__(
        self,
        host: str,
        user: str,
        passwd: str,
        pasv: bool,
        work_dir: str
    ):
        ftp = FTP(host)
        ftp.login(user, passwd)
        logger.info('Logged into FTP host %s', host)

        if work_dir:
            ftp.cwd(work_dir)
            logger.info('Changed a working directory to %s', work_dir)

        # Passive mode is *required* to bypass IHS firewall rules, but does not
        # work on dev machines since they too are behind firewalls
        ftp.set_pasv(pasv)
        logger.info('FTP passive mode set to %s', pasv)

        self.connector = ftp

    def disconnect(self) -> None:
        """Disconnects from FTP silently."""

        self.connector.close()
        logger.info('Disconnected from FTP host %s', self.connector.host)

    def list_files(self, location: str) -> List[str]:
        """Lists both files and directories on FTP server in a specified
        directory."""

        logger.info(
            'Trying to get files list in %s on FTP host %s',
            location,
            self.connector.host
        )
        files = self.connector.nlst(location)
        logger.info(
            'Got files list in %s on FTP host %s',
            location,
            self.connector.host
        )

        return files

    def save_file(self, filename: str, location: str) -> None:
        """Saves a file from FTP to a provided location on a local machine."""

        output = ''
        path = Path(location)
        with path.open(mode='wb') as file_handler:
            output = self.connector.retrbinary(
                f'RETR {filename}', file_handler.write
            )
            logger.info(
                'Contents of FTP file %s saved to %s', filename, location
            )

            if not output.startswith('226'):
                file_handler.unlink()  # type: ignore
                raise RuntimeError(output)


class SFTPConnector(Connector):
    def __init__(
        self,
        host: str,
        user: str,
        passwd: str,
        port: int,
        work_dir: str
    ):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.port = port
        self.work_dir = work_dir
        self.connector = None
        self.transport = None
        self.connect()

    def connect(self):
        transport = Transport(self.host, self.port)
        transport.connect(username=self.user, password=self.passwd)

        sftp = SFTPClient.from_transport(transport)
        logger.info('Logged into SFTP host %s:%s', self.host, self.port)

        if self.work_dir:
            sftp.chdir(self.work_dir)
            logger.info('Changed a working directory to %s', self.work_dir)

        self.connector = sftp
        self.transport = transport

    def disconnect(self):
        """Disconnects from SFTP silently."""

        try:
            self.connector.close()
            self.transport.close()
        except EOFError:
            pass
        logger.info('Disconnected from SFTP host %s', self.transport.hostname)

    def list_files(self, location: str) -> List[str]:  # type: ignore
        """Lists files only on SFTP server in a specified directory."""

        logger.info(
            'Trying to get files list in %s on SFTP host %s',
            location,
            self.transport.hostname
        )

        def _get_files():
            return [
                item.filename
                for item in self.connector.listdir_attr(location)
                if stat.S_IFMT(item.st_mode) != stat.S_IFDIR
            ]

        try:
            files = _get_files()
        except EOFError:
            self.connect()
            files = _get_files()

        logger.info(
            'Got files list in %s on FTP host %s',
            location,
            self.transport.hostname
        )
        return files

    def save_file(self, filename: str, location: str) -> None:
        """Saves a file from SFTP to a provided location on a local machine."""

        def _get_file():
            self.connector.get(filename, location)
            logger.info(
                'Contents of SFTP file %s saved to %s', filename, location
            )

        path = Path(location)

        try:
            try:
                _get_file()
            except EOFError:
                self.connect()
                _get_file()
        except Exception:  # pylint: disable=broad-except
            path.unlink()
            logger.exception(
                'Failed to save filename %s to %s', filename, location
            )
