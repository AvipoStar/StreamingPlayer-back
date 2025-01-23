def convertImgPath(path: str):
    print('convertImgPath', path)
    if path:
        return f"http://79.104.192.137/{path.split('/var/www/')[1]}"