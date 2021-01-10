from ftplib import FTP


def check_anon(ip: str) -> tuple:
    """Check anonymous FTP connection, returns ip if success"""
    try:
        with FTP(ip, timeout=15.0) as ftp:
            ftp.login()
            return (True, ip, ftp.getwelcome().splitlines(False)[0], ftp.dir())
    except:
        return (False, None, None, None)
