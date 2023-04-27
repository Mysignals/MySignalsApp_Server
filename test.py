import enum
class Roles(enum.Enum):
    USER = ('User')
    PROVIDER = ('User','Provider')
    REGISTRAR = ('User','Registrar')

    @staticmethod
    def fetch_names():
        return [c.value for c in Roles]


print(Roles.REGISTRAR.value)

print('User' in Roles.REGISTRAR.value)