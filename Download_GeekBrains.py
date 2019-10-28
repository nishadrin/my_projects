#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json
import os
import urllib.request

import requests
from bs4 import BeautifulSoup

_SEPARATOR = '*' * 50
JSON_COURSES_PATH = os.path.abspath('courses.json')
MAIN_PATH = os.path.abspath('GeekBrains')
MAIN_URL = "https://geekbrains.ru"
COURSES_URL = "https://geekbrains.ru/education"
MAIN_MENU = [
    '1 - Пропарсить и сохранить в json',
    '2 - Скачать из json (файл должен находится по пути:' + \
        f'{COURSES_URL})',
    '3 - Пропарсить и скачать (удаляется json файл)',
    '>4 - Пропарсить и скачать (сохранить json файл)\n',
    'PS: Для скачивания материала может потребоваться много времени' + \
    ' и места на жестком диске',
    ]
ERROR_MESSAGES = [
    f"Не удается скачать ссылки на уроки с основной страницы \
    {COURSES_URL}, возможные проблемы:",
    "1. Нет подключения к интернету",
    "2. Не верный логин и/или пароль от GB",
    "3. GB что то переделали на сайте, и надо редактировать скрипт",
    ]


def write_2_json_file(path, courses):
    with open(path, "w", encoding="utf-8") as file:
        file.write(json.dumps(courses, ensure_ascii=False))
    return True

def read_lines_from_file(path):
    lines = []
    with open(path, "r", encoding="utf-8") as file:
        [lines.append(i.strip()) for i in file.readlines()]
    return lines

def write_lines_in_file(path, lines):
    with open(path, "w", encoding="utf-8") as file:
        [file.writelines(i) for i in lines]
    return True

def save_text_in_file(path, text):
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
    return True

class GoParseGB():

    __step_choise = 'Что будем делать?(Введите цифру): '
    __not_see_file = 'Не вижу файл:'
    __downl_material = 'Скачваем материал...'

    def __init__(self):
        self._continue_download = "0 - Продолжить скачивать"

    def start(self):
        if os.path.exists(JSON_COURSES_PATH):
            MAIN_MENU.insert(0, self._continue_download,)
        print(_SEPARATOR)
        [print(choice) for choice in MAIN_MENU]
        _step = int(input({__step_choise}))
        if _step != 2 and _step != 0:
            _authorization = self.check_authorization()
            _courses_json = self.parsing(_authorization)
        if _step == 1:
            return True
        if _step == 2 or _step == 0:
            if not os.path.exists(JSON_COURSES_PATH):
                print(f'{__not_see_file} {JSON_COURSES_PATH}')
                return False
            with open(JSON_COURSES_PATH, "r", encoding="utf-8") as file:
                _courses_json = json.load(file)
        print(_SEPARATOR, __downl_material, sep='\n')
        _courses_list = [
            _courses_json['lessons'] + _courses_json['chapters'] + \
            _courses_json['interactives']
            ]
        if _step == 0:
            self.downloading(_courses_list, step=_step)
        else:
            self.downloading(_courses_list)
        if _step == 3:
            os.remove(JSON_COURSES_PATH)
        return True

    def check_authorization(self):
        _email, _password = self.login()
        try:
            _authorization = self.authorization(_email, _password)
        except Exception as AuthorizationError:
            _authorization = False
        if not _authorization:
            for error in ERROR_MESSAGES:
                print(error)
        return _authorization

    def login():
        _email = input('Введите email от GB: ')
        _password = input('Введите пароль от GB: ')
        return _email, _password

    def authorization(self, _email, _password):
        _authorization = ParseGB(_email, _password)
        return _authorization

    def parsing(_authorization):
        _authorization.parse()
        _authorization.close_session()
        return True

    def downloading(self, _courses_list, step=1):
        _download = DownloadGB()
        _download.main_download(courses=_courses_list, step=step)
        return True


class ParseGB():
    """docstring for parse_GB

    """


    __save_in_file = 'Сохранили в файл:'
    __parse_one_lesson = 'Парсим каждый урок по отдельности:'
    __parse_educ_url = 'Парсим страницу educations...'
    __parse_educ_url_err = f'Не удалось пропарсить страницу {COURSES_URL}'
    __parse_url = 'Парсим ссылку'
    __parse_vid_web_err = 'Не удалось пропарсить видео/вебинары'
    __parse_inter_err = 'Не удалось пропарсить страницу интерактивы'
    __hw_material_add = 'homework'

    def __init__(
        self, _email, _password):
        self._email = _email
        self._password = _password

        # prepare to authorization
        self.url = f"{MAIN_URL}/login"
        self.connect = requests.Session()
        self.html = self.connect.get(self.url,verify=True)
        self.soup = BeautifulSoup(self.html.content, "html.parser")
        self.hiddenAuthKey = self.soup.find(
            'input', {'name': 'authenticity_token'})['value']

        # authorization
        self.connect.get(self.url,verify=True)
        self.login_data = {
            "utf8": "✓", "authenticity_token": self.hiddenAuthKey,
            "user[email]": self._email, "user[password]": self._password,
            "user[remember_me]": "0"
            }
        self.connect.post(
            MAIN_URL,
            data=self.login_data,
            headers={"Referer": f"{MAIN_URL}/login"}
            )

    def close_session(self):
        self.connect.close()


    def is_study_groups(self, url):
        if "study_groups" in url:
            return True
        return False

    def is_lessons(self, url):
        if "lessons" in url:
            return True
        return False

    def is_chapters(self, url):
        if "chapters" in url:
            return True
        return False


    def parse(self):
        _courses = self.parse_lessons()
        write_2_json_file(path=JSON_COURSES_PATH, courses=_courses)
        print(f'{__save_in_file} {JSON_COURSES_PATH}')
        return True

    def parse_lessons(self):
        _lessons, _chapters, _interactives = self.check_parse_courses()
        if not _lessons:
            return False
        print(_SEPARATOR, __parse_one_lesson, sep='\n')
        _lessons_list = self.parse_many_courses(_lessons)
        _chapters_list = self.parse_many_courses(_chapters)
        _interactives_list = self.parse_many_courses(_interactives)
        _courses_dict = {
            'lessons': _lessons_list, 'chapters': _chapters_list,
            'interactives': _interactives_list
            }
        return _courses_dict

    def check_parse_courses(self):
        print(_SEPARATOR, __parse_educ_url, sep='\n')
        try:
            _lessons, _chapters, _interactives = self.parse_courses()
        except Exception as EducationParseError:
            print(_SEPARATOR, __parse_educ_url_err, sep='\n')
            return False, False, False
        return _lessons, _chapters, _interactives

    def parse_many_courses(self, courses):
        _courses_list = []
        for i in courses:
            print(f'{__parse_url} {i}')
            if 'lessons' in i or 'chapters' in i:
                try:
                    _one_course = self.parse_lesson_or_chapter(i)
                except Exception as LessonChapterError:
                    print(__parse_vid_web_err)
                    return False
            if 'study_groups' in i:
                try:
                    _one_course = self.parse_interactive(i)
                except Exception as InteractiveError:
                    print(__parse_inter_err)
                    return False
            _courses_list.append(_one_course)
        return _courses_list

    def parse_courses(self):
        _filehtml = self.connect.get(COURSES_URL)
        _soup_all_courses = BeautifulSoup(_filehtml.content, "html.parser")
        _find_json_courses = _soup_all_courses.find(
            'script', {"data-component-name": "EducationPage"}
            ).text
        _json_courses = json.loads(_find_json_courses)
        _webinars_and_interactives = _json_courses['data']['lessons']
        _videos = _json_courses['data']['chapters']
        _interactives_urls = []
        _webinars_urls = []
        _videos_urls = []
        for key, value in _webinars_and_interactives.items():
            if self.is_study_groups(value['link']):
                _interactives_urls.append(
                    f"{MAIN_URL}/{value['link']}/videos/{value['id']}"
                    )
            if self.is_lessons(value['link']):
                _webinars_urls.append(f"{MAIN_URL}/{value['link']}")
        for key, value in _videos.items():
            _videos_urls.append(f"{MAIN_URL}/{value['link']}")
        return _webinars_urls, _videos_urls, _interactives_urls

    def parse_lesson_or_chapter(self, url):
        filehtml = self.connect.get(url)
        soup = BeautifulSoup(filehtml.content, "html.parser")
        links_list = []
        name_list = []
        for i in soup.findAll("li", {"class": "lesson-contents__list-item"}):
            links_list.append(i.find("a")['href'])
            name_list.append(i.find("a").text)
        links = {"name_list": name_list, "links_list": links_list}
        course_name = soup.find("span", {"class": "course-title"}).text
        lesson_name = soup.find("h3", {"class": "title"}).text
        comment = soup.find("div", {"class": "lesson-content__content"})
        if comment:
            comment = comment.text
        else:
            comment = None
        dz = None
        if is_lessons(url):
            filehtml_homework = self.connect.get(f'{url}/{__hw_material_add}')
            homework = BeautifulSoup(filehtml_homework.content, "html.parser")
            dz = homework.find("div", {"class": "task-block-teacher"})
            if dz:
                dz = dz.text
        is_downloaded = False
        dic = {
            "course_name": course_name, "lesson_name": lesson_name,
            "content_url": url, "comment": comment, "links": links,
            "dz": dz, "is_downloaded": is_downloaded
            }
        return dic

    def parse_interactive(self, url):
        filehtml = self.connect.get(url)
        soup = BeautifulSoup(filehtml.content, "html.parser")
        links_list = []
        name_list = []
        for i in soup.findAll("div", {"class": "lesson-contents"}):
            links_list.append(i.find("a")['href'])
            name_list.append(i.find("a").text)
        links = {"name_list": name_list, "links_list": links_list}
        course_name = soup.find("span", {"class": "course-title"}).text
        lesson_name = soup.find("h3", {"class": "title"}).text
        url_2_parse_hw = re.findall(r'\/videos\/\d+', url) # TODO re.findall c [0]
        videos_number = re.findall(r'\/\d+', url_2_parse_hw[0]) # TODO re.findall c [0]
        url_2_parse_course = re.findall(r'study_groups/\d+/videos/', url) # TODO re.findall c [0]
        url_2_parse_course_number = re.findall(r'/\d+/', url_2_parse_course[0]) # TODO re.findall c [0]
        link_dz = f'{MAIN_URL}/study_groups' + \
            f'{url_2_parse_course_number[0]}homeworks{videos_number[0]}'
        filehtml_hw = self.connect.get(link_dz)
        soup_hw = BeautifulSoup(filehtml_hw.content, "html.parser")
        dz = soup_hw.find("div", {"class": "homework-description"}).text
        comment = None
        is_downloaded = False
        dic = {
            "course_name": course_name, "lesson_name": lesson_name,
            "content_url": url, "links": links, "comment": comment, "dz": dz,
            "is_downloaded": is_downloaded
            }
        return dic


class DownloadGB():
    """docstring for DownloadGB.

    """
    __was_downl_info = (
        ' Файл уже был скачен ранее , если скачен не корректно или не скачен \
            (1. пропустить):',
        '1. удалите багованные файлы с компьютера',
        '2. и в начале использования скрипта введите цифру 2\n'
        )
    __attention = 'Важные объявление.txt'
    __home_work = 'Домашнее задание.txt'
    __urls = 'Ссылки.txt'
    __unexpexted_err = 'cкачать не могу, по неизвестным причинам'
    __acsses_err = 'Доступ запрещен, до сайта:'
    __google_sheet = 'Скачать не могу, так как это ссылка на google sheets \
        страницу:'
    __web_url = 'Скачать не могу, так как это ссылка на Web-страницу:'
    __download_file = 'Скачали файл'
    __arleady_exists = 'Уже существует'
    __create_path = 'Создана папка'
    __save_url_2_file = 'Сохранили сслыку в файл:'
    __html = "html"
    __app_bin = 'application/binary'
    __docs_google = "docs.google.com"
    __drive_google = "drive.google.com"

    def is_web_url(self, content_type):
        if content_type == None or __html in content_type or \
                __app_bin in content_type:
            return True
        return False

    def is_google_drive(self, _file2download):
        if __drive_google in _file2download or __docs_google in _file2download:
            return True
        return False

    def main_download(self, courses, step):
        self.create_or_download(f'{MAIN_PATH}/')
        for lesson in courses:
            print()
            _course_name, _lesson_name = self.replaces_for_paths(
                lesson['course_name'], lesson['lesson_name']
                )

            if step == 0 and lesson['is_downloaded']:
                way_path = f'{MAIN_PATH}/{_course_name}/{_lesson_name}/'
                __was_downl_info.insert(
                    0,
                    f'{_lesson_name}({lesson["content_url"]})'
                    )
                __was_downl_info.append(_SEPARATOR)
                [print(i) for i in __was_downl_info]
                continue

            # создаем папки
            self.create_or_download(f'{MAIN_PATH}/{_course_name}/')
            self.create_or_download(
                f'{MAIN_PATH}/{_course_name}/{_lesson_name}/'
                )

            # скачаиваем инфу
            if lesson['comment'] != None:
                self.create_or_download(
                    f'{MAIN_PATH}/{_course_name}/{_lesson_name}/{__attention}',
                    text=lesson['comment']
                    )
            if lesson['dz'] != None:
                self.create_or_download(
                    f'{MAIN_PATH}/{_course_name}/{_lesson_name}/{__home_work}',
                    text=lesson['dz']
                    )

            _links_list = []
            for n in _links_lists:
                _links_list.append(n)
            _links_name_list = []
            _name_list = lesson['links']['name_list']
            _links_lists = lesson['links']['links_list']
            for n in _name_list:
                _links_name_list.append(n)
            _names = self.name_file(
                links_name_list=_links_name_list,
                links_list=_links_list
                )

            n = 0
            while n+1 <= len(_links_list):
                self.create_or_download(
                f'{MAIN_PATH}/{_course_name}/{_lesson_name}/{_names[n]}'
                ),
                _file2download = _links_list[n],
                _pwd_path = f'{MAIN_PATH}/{_course_name}/{_lesson_name}'
                n += 1
            lesson['is_downloaded'] = True
        _courses = {
            'lessons': lessons_list,
            'chapters': chapters_list,
            'interactives': interactives_list
            }

        write_2_json_file(JSON_COURSES_PATH, courses=_courses)
        return True

    def check_download_all(self, _file2download):
        try:
            request_url = requests.head(_file2download)
        except Exception as e:
            request_url = None
        try:
            connection = request_url.headers['Connection']
        except Exception as e:
            connection = None
        try:
            content_type = request_url.headers['content-type']
        except Exception as e:
            content_type = None
        return request_url, connection, content_type

    def download_all(self, path, _file2download, _pwd_path):
        request_url, connection, content_type = self.check_download_all(
            _file2download
            )
        if request_url == None:
            print(f"{_file2download} {__unexpexted_err}")
        if connection == 'close':
            print(f'{__acsses_err} {_file2download}')
        if self.is_web_url(content_type):
            if content_type != None and self.is_google_drive(_file2download):
                print(f"{__google_sheet} {_file2download}")
            else:
                print(f"{__web_url} {_file2download}")
        else:
            urllib.request.urlretrieve(_file2download, path)
            print(f"{__download_file} {path}")
            return True

        self.resave_urls(_file2download, _pwd_path)

    def create_or_download(self, path, _pwd_path=None, _file2download=None, text=None):
        if os.path.exists(path):
            print(f'{__arleady_exists} {path}')
        elif os.path.exists(f'{_pwd_path}/{__urls}'):
            print(f'{__arleady_exists} {_pwd_path}/{__urls}')
        else:
            if _file2download==None and text==None:
                os.mkdir(path):
                print(f"{__create_path} {path}")
            elif text != None:
                save_text_in_file(path, text)
                print(f"__create_path {path}")
            elif _file2download != None:
                self.download_all(path, _file2download, _pwd_path)

    def resave_urls(self, file2download, pwd_path):
        path = f'{pwd_path}/{__urls}'
        lines = []
        if os.path.exists(path):
            lines = read_lines_from_file(path)
        lines.append(file2download)
        lines = set(lines)
        write_lines_in_file(path, lines)
        print(f'{__save_url_2_file} {path}')
        return True

    def replaces_for_paths(_course_name, _lesson_name):
        # заменяем все "\" и "/" на "_", что бы при скачивании порграмма
        # не считала, что это путь
        _course_name = _course_name.replace(_course_name, '\\', "_")
        _course_name = _course_name.replace(_course_name, "/", "_")
        _lesson_name = _lesson_name.replace(_lesson_name, '\\', "_")
        _lesson_name = _lesson_name.replace(_lesson_name, "/", "_")
        return _course_name, _lesson_name

    def name_file(self, links_name_list, links_list):
        n = 0
        names = []
        while n+1 <= len(links_list):
            if __docs_google in links_list[n] or \
                __drive_google in links_list[n]:
                names.append(links_name_list[n])
            else:
                expansion_link = re.findall(r"\.\w+$", links_list[n])
                expansion_name = re.findall(r"\.\w+$", links_name_list[n])
                if expansion_link == expansion_name:
                    names.append(links_name_list[n])
                else:
                    names.append(f'{links_name_list[n]}{expansion_link[0]}')
            n +=1
        return names

def main():
    parse = GoParseGB()
    return parse.start()

if __name__ == '__main__':
    __thanks = 'Спасибо, за то, что воспользовались скриптом!'
    __offers = ('\nЖаль, что Вам не удлось воспользоваться скриптом.',
        "По вопросами и предложениям можно писать в Телеграм: @nishadrin \
        (https://t.me/nishadrin)")

    if main():
        print(__thanks)
    else:
        [print(i, sep='\n') for i in __offers]
