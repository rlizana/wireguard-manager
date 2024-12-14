
class Config:

    def __init__(self, **args):
        self.__dict__.update(args)

    def get(self, key, default=None):
        return getattr(self, key, default)

    def __str__(self) -> str:
        return str(self.__dict__)

    def __repr__(self) -> str:
        return self.__str__()
