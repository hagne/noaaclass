class Command(object):
    def do(self, conn):
        raise Exception('Subclass responsability!')


class api(object):
    def __init__(self, connection):
        self.connection = connection
