from pprint import pprint

from secrets import *
from config import *
from parse_gb import AuthorizationGB


def main():
    interactives = {'5482': [30096, 30097, 30098, 30099, 30100, 30101, 30102, 30103, 30104, 30105],
     '5497': [30186, 30187, 30188, 30189, 30190]}
    login = AuthorizationGB()
    session = login.connect()
    if session is None:
        login.disconnect(session)
        return None

    interactive = session.parse_interactives(interactives)
    login.disconnect(session)
    return interactive

if __name__ == '__main__':
    pprint(main())
