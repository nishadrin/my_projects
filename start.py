from backend.config import *

class GoParseGB():

    __step_choise = 'Что будем делать?(Введите цифру): '
    __not_see_file = 'Не вижу файл:'
    __downl_material = 'Скачваем материал...'
    _continue_download = "0 - Продолжить скачивать"

    def start(self):
        step = -1
        if os.path.exists(JSON_COURSES_PATH):
            MAIN_MENU.insert(0, self._continue_download,)
        while step not in [0, 1, 2, 3, 4, 5]:
            if step == 5:
                return True
            print(SEPARATOR)
            [print(choice) for choice in MAIN_MENU]
            step = int(input(self.__step_choise))

        if step != 2 and step != 0:
            authorization = self.check_authorization()
            courses_json = self.parsing(authorization)
        if step == 1:
            return True


def main():
    return GoParseGB().start()

if __name__ == '__main__':
    __thanks = '\nСпасибо, за то, что воспользовались скриптом!\n'
    __offers = ('\nЖаль, что Вам не удлось воспользоваться скриптом.',
        "По вопросами и предложениям можно писать в Телеграм: @nishadrin \
        (https://t.me/nishadrin)\n")

    if main():
        print(__thanks)
    else:
        [print(i) for i in __offers]
