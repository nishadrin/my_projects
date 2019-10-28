#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json
import os
import urllib.request

import requests
from bs4 import BeautifulSoup


class GoParseGB():
    def __init__(self):
        # init variables
        self._continue_download = "0 - Продолжить скачивать"
        self._courses_path = os.path.abspath('courses.json')
        self._separator = '*' * 50
        self._main_url = "https://geekbrains.ru"
        self._url_courses = "https://geekbrains.ru/education"
        self._main_path = os.path.abspath('GeekBrains')
        self.error_messages = [
            "Не удается скачать ссылки на уроки с основной страницы " +\
            f"{self._url_courses}, возможные проблемы:",
            "1. Нет подключения к интернету",
            "2. Не верный логин и/или пароль от GB",
            "3. GB что то переделали на сайте, и надо редактировать скрипт",
            ]
        self._main_menu = [
            '1 - Пропарсить и сохранить в json',
            '2 - Скачать из json (файл должен находится по пути:' + \
                f'{self._url_courses})',
            '3 - Пропарсить и скачать (удаляется json файл)',
            '>4 - Пропарсить и скачать (сохранить json файл)\n',
            'PS: Для скачивания материала может потребоваться много времени' + \
            ' и места на жестком диске',
            ]


    def is_courses_path_exists(self):
        return os.path.exists(self._courses_path)

    def start(self):
        if self.is_courses_path_exists():
            self._main_menu.insert(0, self._continue_download,)
        print(self._separator)
        for choice in self._main_menu:
            print(choice)
        _step = int(input('Что будем делать?(Введите цифру) '))
        print(self._separator)
        if _step != 2 and _step != 0:
            _authorization = self.check_authorization()
            _courses_json = self.parsing(_authorization)
            _authorization.close_session()
        if _step == 1:
            return True
        if _step == 2 or _step == 0:
            if not self.is_courses_path_exists():
                print(f'\nНе вижу файл: {self._courses_path}')
                return False
            with open(self._courses_path, "r", encoding="utf-8") as file:
                _courses_json = json.load(file)
        print(self._separator)
        print('Скачваем материал...')
        _lessons_list = _courses_json['lessons']
        _chapters_list = _courses_json['chapters']
        _interactives_list = _courses_json['interactives']
        _courses_list = (_lessons_list+_chapters_list+_interactives_list)
        if _step == 0:
            self.downloading(_courses_list, step=_step)
        else:
            self.downloading(_courses_list)
        if _step == 3:
            os.remove(self._courses_path)
        return True

    def check_authorization(self):
        _email, _password = self.login()
        try:
            _authorization = self.authorization(_email, _password)
        except Exception as AuthorizationError:
            _authorization = False
        if not _authorization:
            for error in self.error_messages:
                print(error)
        return _authorization

    def login(cls):
        _email = input('Введите email от GB: ')
        _password = input('Введите пароль от GB: ')
        return _email, _password

    def authorization(self, _email, _password):
        _authorization = ParseGB(
            _email, _password, _separator=self._separator,
            _main_url=self._main_url, _url_courses=self._url_courses,
            _main_path=self._main_path, _courses_path=self._courses_path,
            )
        return _authorization

    def parsing(cls, _authorization):
        _authorization.parse()
        return True

    def downloading(self, _courses_list, step=1):
        _download = DownloadGB(
            _separator=self._separator, _main_url=self._main_url,
            _url_courses=self._url_courses, _main_path=self._main_path,
             _courses_path=self._courses_path,
            )
        _download.download(courses=_courses_list, step=step)
        return True


class ParseGB():
    """docstring for parse_GB

    """


    # инициируем авторизированную сессию
    def __init__(
        self, _email, _password, _separator, _main_url, _url_courses,
        _main_path, _courses_path
        ):
        self._email = _email
        self._password = _password
        self._separator = _separator
        self._main_url = _main_url
        self._url_courses = _url_courses
        self._main_path = _main_path
        self._courses_path = _courses_path

        # prepare to authorization
        self.url = f"{self._main_url}/login"
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
            self._main_url,
            data=self.login_data,
            headers={"Referer": f"{self._main_url}/login"}
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
        self.write_2_json_file(path=self._courses_path, courses=_courses)
        return True

    def parse_lessons(self):
        _lessons, _chapters, _interactives = self.check_parse_courses()
        if not _lessons:
            return False
        print(self._separator, 'Парсим каждый урок по отдельности:', sep='\n')
        _lessons_list = self.parse_many_courses(_lessons)
        _chapters_list = self.parse_many_courses(_chapters)
        _interactives_list = self.parse_many_courses(_interactives)
        _courses_dict = {
            'lessons': _lessons_list, 'chapters': _chapters_list,
            'interactives': _interactives_list
            }
        return _courses_dict

    def write_2_json_file(cls, path, courses):
        with open(path, "w", encoding="utf-8") as file:
            file.write(json.dumps(courses, ensure_ascii=False))
        print(f'Сохранили в файл: {path}')

    def check_parse_courses(self):
        print(self._separator, 'Парсим страницу educations...', sep='\n')
        try:
            _lessons, _chapters, _interactives = self.parse_courses()
        except Exception as EducationParseError:
            print(f'Не удалось пропарсить страницу {self._url_courses}')
            return False, False, False
        return _lessons, _chapters, _interactives

    def parse_many_courses(self, courses):
        _courses_list = list()
        for i in courses:
            print(f'Парсим ссылку {i}')
            if 'lessons' in i or 'chapters' in i:
                try:
                    _one_course = self.parse_lesson_or_chapter(i)
                except Exception as LessonChapterError:
                    print('Не удалось пропарсить страницу видео/вебинары')
                    return False
            if 'study_groups' in i:
                try:
                    _one_course = self.parse_interactive(i)
                except Exception as InteractiveError:
                    print('Не удалось пропарсить страницу интерактивы')
                    return False
            _courses_list.append(_one_course)
        return _courses_list

    # Получаем ссылки на доступные уроки, вебинары, интерактивы
    def parse_courses(self):
        _filehtml = self.connect.get(self._url_courses)
        _soup_all_courses = BeautifulSoup(_filehtml.content, "html.parser")
        _find_json_courses = _soup_all_courses.find(
            'script', {"data-component-name": "EducationPage"}
            ).text
        _json_courses = json.loads(_find_json_courses)
        _webinars_and_interactives = _json_courses['data']['lessons']
        _videos = _json_courses['data']['chapters']
        _interactives_urls = list()
        _webinars_urls = list()
        _videos_urls = list()
        for key, value in _webinars_and_interactives.items():
            if self.is_study_groups(value['link']):
                _interactives_urls.append(
                    f"{self._main_url}/{value['link']}/videos/{value['id']}"
                    )
            if self.is_lessons(value['link']):
                _webinars_urls.append(f"{self._main_url}/{value['link']}")
        for key, value in _videos.items():
            _videos_urls.append(f"{self._main_url}/{value['link']}")
        return _webinars_urls, _videos_urls, _interactives_urls

    def parse_lesson_or_chapter(self, url):
        filehtml = self.connect.get(url)
        soup = BeautifulSoup(filehtml.content, "html.parser")
        links_list = list()
        name_list = list()
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
        if "/lessons" in url:
            filehtml_homework = self.connect.get(url + "/homework")
            homework = BeautifulSoup(filehtml_homework.content, "html.parser")
            dz = homework.find("div", { "class" : "task-block-teacher" })
            if dz:
                dz = dz.text
            else:
                dz = None
        else:
            dz = None
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
        links_list = list()
        name_list = list()
        for i in soup.findAll("div", {"class": "lesson-contents"}):
            links_list.append(i.find("a")['href'])
            name_list.append(i.find("a").text)
        links = {"name_list": name_list, "links_list": links_list}
        course_name = soup.find("span", {"class": "course-title"}).text
        lesson_name = soup.find("h3", {"class": "title"}).text
        url_2_parse_hw = re.findall(r'\/videos\/\d+', url)
        videos_number = re.findall(r'\/\d+', url_2_parse_hw[0])
        url_2_parse_course = re.findall(r'study_groups/\d+/videos/', url)
        url_2_parse_course_number = re.findall(r'/\d+/', url_2_parse_course[0])
        link_dz = f'{self._main_url}/study_groups' + \
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

    def __init__(
        self, _separator, _main_url, _url_courses,
        _main_path, _courses_path
        ):
        self._separator = _separator
        self._main_url = _main_url
        self._url_courses = _url_courses
        self._main_path = _main_path
        self._courses_path = _courses_path


    def save_urls(self, file2download, pwd_path):
        path = pwd_path + '/Ссылки.txt'
        lines = list()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as file:
                lines = [i.strip() for i in file.readlines()]
                read_file = file.readlines()
                for i in read_file:
                    line = i.strip()
                    lines.append(line)
        lines.append(file2download)
        lines = set(lines)
        with open(path, "w", encoding="utf-8") as file:
            for i in lines:
                file.write(i + '\n')
        print(f'Сохранили сслыку в файл: {path}')

    def replace_for_paths(cls, _course_name, _lesson_name):
        # заменяем все "\" и "/" на "_", что бы при скачивании порграмма
        # не считала, что это путь
        _course_name = re.sub(r'\\', "_", _course_name)
        _course_name = re.sub(r'/', "_", _course_name)
        _lesson_name = re.sub(r'\\', "_", _lesson_name)
        _lesson_name = re.sub(r'/', "_", _lesson_name)
        return _course_name, _lesson_name

    def download(self, courses, step):
        for lesson in courses:
            print()
            _course_name = lesson['course_name']
            _lesson_name = lesson['lesson_name']
            _course_name, _lesson_name = self.replace_for_paths(
                _course_name, _lesson_name
                )
            _name_list = lesson['links']['name_list']
            _links_lists = lesson['links']['links_list']
            if step == 0 and lesson['is_downloaded']:
                way_path = f'{self._main_path}/{_course_name}/{_lesson_name}/'
                downloaded_message = (
                    f'Курс {lesson["content_url"]} уже был скачен ранее , ' + \
                    'если скачен не корректно или не скачен (1 шаг пропустить):',
                    f'1. удалите файлы с компьютера по пути: {way_path}',
                    '2. и в начале использования скрипта введите цифру 2'
                    )
                print('*' * 50)
                for info in downloaded_message:
                    print(info)
                continue
        # создаем папки
        self.create_or_download(f'{self._main_path}/{_course_name}/')
        self.create_or_download(
            f'{self._main_path}/{_course_name}/{_lesson_name}/'
            )
        # скачаиваем инфу
        if lesson['comment'] != None:
            download.create_or_download(
                f'{self._main_path}/{_course_name}/{_lesson_name}/' + \
                    'Важные объявление.txt',
                text=lesson['comment']
                )
        if lesson['dz'] != None:
            download.create_or_download(
                f'{self._main_path}/{_course_name}/{_lesson_name}/' + \
                    'Домашнее задание.txt',
                text=lesson['dz']
                )
        _links_list = list()
        for n in _links_lists:
            _links_list.append(n)
        _links_name_list = list()
        for n in name_list:
            _links_name_list.append(n)
        _names = download.name_file(
            links_name_list=_links_name_list,
            links_list=_links_list
            )
        n = 0
        while n+1 <= len(_links_list):
            download.create_or_download(
                f'{self._main_path}/{_course_name}/{_lesson_name}/{_names[n]}'
                ),
            _file2download = _links_list[n],
            _pwd_path = f'{self._main_path}/{_course_name}/{_lesson_name}'
            n += 1
        lesson['is_downloaded'] = True
        _list_save = {
            'lessons': lessons_list,
            'chapters': chapters_list,
            'interactives': interactives_list
            }
        with open(self._courses_path, "w", encoding="utf-8") as file:
            file.write(json.dumps(_list_save, ensure_ascii=False))
        return True

    def download_all(self, path, _file2download, _pwd_path):
        try:
            request_url = requests.head(_file2download)
        except Exception as e:
            request_url = None
        if request_url == None:
            print(f"{_file2download} cкачать не могу, по непонятным причинам")
            self.save_urls(_file2download, _pwd_path)
            return False
        try:
            connection = request_url.headers['Connection']
        except Exception as e:
            connection = None
        if connection == 'close':
            print(f'Доступ к ресурсу {_file2download} запрещен')
            self.save_urls(_file2download, _pwd_path)
            return False
        try:
            content_type = request_url.headers['content-type']
        except Exception as e:
            content_type = None
        if content_type == None or "html" in content_type or \
                'application/binary' in content_type:
            if content_type != None and "drive.google.com" in _file2download \
                    or "docs.google.com" in _file2download:
                print("Скачать не могу, так как это ссылка на google sheets " + \
                    f"страницу: {_file2download}"
                    )
                self.save_urls(_file2download, _pwd_path)
            else:
                print("Скачать не могу, так как это ссылка на веб " + \
                    f"страницу: {_file2download}"
                    )
                self.save_urls(_file2download, _pwd_path)
        else:
            urllib.request.urlretrieve(_file2download, path)
            print(f"Скачали файл {path}")

    def create_or_download(self, path, _pwd_path=None, _file2download=None, text=None):
        if os.path.exists(path):
            print(f'Уже существует {path}')
        elif os.path.exists(f'{_pwd_path}/Ссылки.txt'):
            print(f'Уже существует {_pwd_path}/Ссылки.txt')
        else:
            if _file2download==None and text==None:
                os.mkdir(path)
                print(f"Создана папка {path}")

            elif text != None:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"Создан файл {path}")

            elif _file2download != None:
                self.download_all(path, _file2download, _pwd_path)

    def name_file(self, links_name_list, links_list):
            n = 0
            names = list()
            while n+1 <= len(links_list):
                if ".google.com" in links_list[n]:
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
    if main():
        print('Спасибо, за то, что воспользовались скриптом!')
    else:
        print('\nЖаль, что Вам не удлось воспользоваться скриптом.',
            "По вопросами и предложениям можно писать в Телеграм: @nishadrin" +\
            "(https://t.me/nishadrin)", sep='\n')
