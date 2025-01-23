def convertDate(date: str):
    if date:
        buff = str(date).split('-')
        return f'{buff[2]}.{buff[1]}.{buff[0]}'
