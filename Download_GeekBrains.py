#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json
import os
import urllib.request

import requests
from bs4 import BeautifulSoup


SEPARATOR = '*' * 50
JSON_COURSES_PATH = os.path.abspath('courses.json')
MAIN_PATH = os.path.abspath('GeekBrains')
MAIN_URL = "https://geekbrains.ru"
COURSES_URL = "https://geekbrains.ru/education"
MAIN_MENU = [
    '1 - Пропарсить и сохранить в json',
    f'2 - Скачать из json (файл должен находится по пути: {COURSES_URL})',
    '3 - Пропарсить и скачать (удаляется json файл)',
    '4 - Пропарсить и скачать (сохранить json файл)\n',
    'PS: Для скачивания материала может потребоваться много времени \
и места на жестком диске',
    ]
ERROR_MESSAGES = [
    f"Не удается скачать ссылки на уроки с основной страницы {COURSES_URL}, \
возможные проблемы:",
    "1. Нет подключения к интернету",
    "2. Не верный логин и/или пароль от GB",
    "3. GB что то переделали на сайте, и надо редактировать скрипт",
    ]


def write_to_json_file(path, courses):
    with open(path, "w", encoding="utf-8") as file:
        file.write(json.dumps(courses, ensure_ascii=False))
    return True

def read_lines_from_file(path):
    with open(path, "r", encoding="utf-8") as file:
        return [line.strip() for line in file.readlines()]

def write_lines_in_file(path, lines):
    with open(path, "w", encoding="utf-8") as file:
        [file.writelines(line) for line in lines]
    return True

def save_text_in_file(path, text):
    with open(path, "w", encoding="utf-8") as file:
        file.write(text)
    return True

class GoParseGB():

    __step_choise = 'Что будем делать?(Введите цифру): '
    __not_see_file = 'Не вижу файл:'
    __downl_material = 'Скачваем материал...'
    _continue_download = "0 - Продолжить скачивать"


    def start(self):
        step = -1
        if os.path.exists(JSON_COURSES_PATH):
            MAIN_MENU.insert(0, self._continue_download,)
        while step not in [0, 1, 2, 3, 4]:
            print(SEPARATOR)
            [print(choice) for choice in MAIN_MENU]
            step = int(input(self.__step_choise))

        if step != 2 and step != 0:
            authorization = self.check_authorization()
            courses_json = self.parsing(authorization)
        if step == 1:
            return True
        if step == 2 or step == 0:
            if not os.path.exists(JSON_COURSES_PATH):
                print(f'{self.__not_see_file} {JSON_COURSES_PATH}')
                return False
            with open(JSON_COURSES_PATH, "r", encoding="utf-8") as file:
                courses_json = json.load(file)
        print(SEPARATOR, self.__downl_material, sep='\n')
        courses_list = {
            'lessons': courses_json['lessons'],
            'chapters': courses_json['chapters'],
            'interactives': courses_json['interactives']
            }
        if step == 0:
            self.downloading(courses_list, step=step)
        else:
            self.downloading(courses_list)
        if step == 3:
            os.remove(JSON_COURSES_PATH)
        return True

    def check_authorization(self):
        email, password = self.login()
        try:
            authorization = self.authorization(email, password)
        except Exception as AuthorizationError:
            authorization = None
        if authorization is None:
            [print(error) for error in ERROR_MESSAGES]
            return None
        return authorization

    def login(self):
        email = input('Введите email от GB: ')
        password = input('Введите пароль от GB: ')
        return email, password

    def authorization(self, email, password):
        authorization = ParseGB(email, password)
        return authorization

    def parsing(self, authorization):
        authorization.parse()
        authorization.close_session()
        return True

    def downloading(self, courses_list, step=1):
        _download = DownloadGB()
        _download.main_download(courses=courses_list, step=step)
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

    def __init__(self, email, password):
        self.email = email
        self.password = password

        # prepare to authorization
        self.url = f"{MAIN_URL}/login"
        self.connect = requests.Session()
        self.html = self.connect.get(self.url,verify=True)
        self.soup = BeautifulSoup(self.html.content, "html.parser")
        self.hidden_auth_token = self.soup.find(
            'input', {'name': 'authenticity_token'})['value']

        # authorization
        self.connect.get(self.url,verify=True)
        self.login_data = {
            "utf8": "✓", "authenticity_token": self.hidden_auth_token,
            "user[email]": self.email, "user[password]": self.password,
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


    def get_soup(self, url):
        html = self.connect.get(url)
        return BeautifulSoup(html.content, "html.parser")

    def parse(self):
        courses = self.parse_lessons()
        write_to_json_file(path=JSON_COURSES_PATH, courses=courses)
        print(SEPARATOR)
        print(f"{self.__save_in_file} {JSON_COURSES_PATH}")
        return True

    def parse_lessons(self):
        _lessons, _chapters, _interactives = self.check_parse_courses()
        if not _lessons:
            return None
        print(SEPARATOR, self.__parse_one_lesson, sep='\n')
        print(SEPARATOR)
        _lessons_list = self.parse_many_courses(_lessons)
        _chapters_list = self.parse_many_courses(_chapters)
        _interactives_list = self.parse_many_courses(_interactives)
        courses_dict = {
            'lessons': _lessons_list, 'chapters': _chapters_list,
            'interactives': _interactives_list
            }
        return courses_dict

    def check_parse_courses(self):
        print(SEPARATOR, self.__parse_educ_url, sep='\n')
        try:
            _lessons, _chapters, _interactives = self.parse_courses()
        except Exception as EducationParseError:
            print(SEPARATOR, self.__parse_educ_url_err, sep='\n')
            return None, None, None
        return _lessons, _chapters, _interactives

    def parse_many_courses(self, courses):
        courses_list = []
        for i in courses:
            print(f'{self.__parse_url} {i}')
            if 'lessons' in i or 'chapters' in i:
                try:
                    _one_course = self.parse_lesson_or_chapter(i)
                except Exception as LessonChapterError:
                    print(self.__parse_vid_web_err)
                    return False
            if 'study_groups' in i:
                try:
                    _one_course = self.parse_interactive(i)
                except Exception as InteractiveError:
                    print(self.__parse_inter_err)
                    return False
            courses_list.append(_one_course)
        return courses_list

    def parse_courses(self):
        soup_courses = self.get_soup(COURSES_URL)
        find_courses = soup_courses.find(
            'script', {"data-component-name": "EducationPage"}
            ).text
        load_courses = json.loads(find_courses)
        webinars_and_interactives = load_courses['data']['lessons']
        videos = load_courses['data']['chapters']
        interactives_urls = []
        webinars_urls = []
        videos_urls = []
        for key, lesson in webinars_and_interactives.items():
            if self.is_study_groups(lesson['link']):
                interactives_urls.append(
                    f"{MAIN_URL}/{lesson['link']}/videos/{lesson['id']}"
                    )
            if self.is_lessons(lesson['link']):
                webinars_urls.append(f"{MAIN_URL}/{lesson['link']}")
        for key, video in videos.items():
            videos_urls.append(f"{MAIN_URL}/{video['link']}")
        return webinars_urls, videos_urls, interactives_urls

    def parse_lesson_or_chapter(self, url):
        lesson_soup = self.get_soup(url)
        links_list = []
        name_list = []
        for i in lesson_soup.findAll(
                "li",
                {"class": "lesson-contents__list-item"}
                ):
            links_list.append(i.find("a")['href'])
            name_list.append(i.find("a").text)

        links = {"name_list": name_list, "links_list": links_list}
        course_name = lesson_soup.find("span", {"class": "course-title"}).text
        lesson_name = lesson_soup.find("h3", {"class": "title"}).text
        comment = lesson_soup.find("div", {"class": "lesson-content__content"})
        is_downloaded = False

        if comment:
            comment = comment.text
        else:
            comment = None
        homework = None
        if self.is_lessons(url):
            homework_soup = self.get_soup(f'{url}/{self.__hw_material_add}')
            homework = homework_soup.find(
                "div",
                {"class": "task-block-teacher"}
                )
            if homework:
                homework = homework.text
        dic = {
            "course_name": course_name, "lesson_name": lesson_name,
            "content_url": url, "comment": comment, "links": links,
            "homework": homework, "is_downloaded": is_downloaded
            }
        return dic

    def parse_interactive(self, url):
        interactive_soup = self.get_soup(url)
        links_list = []
        name_list = []
        for i in interactive_soup.findAll("div", {"class": "lesson-contents"}):
            links_list.append(i.find("a")['href'])
            name_list.append(i.find("a").text)
        link_hw = self.regex_inter_hw_url(url)
        soup_hw = self.get_soup(link_hw)

        homework = soup_hw.find("div", {"class": "homework-description"}).text
        course_name = interactive_soup.find(
            "span",
            {"class": "course-title"}
            ).text
        lesson_name = interactive_soup.find("h3", {"class": "title"}).text
        links = {"name_list": name_list, "links_list": links_list}
        return {
            "course_name": course_name, "lesson_name": lesson_name,
            "content_url": url, "links": links, "comment": comment,
            "homework": None, "is_downloaded": False
            }

    def regex_inter_hw_url(self, url): # TODO может можно 2 запросами?
        url_to_parse_hw = re.findall(r'\/videos\/\d+', url) # TODO re.findall c [0]
        videos_number = re.findall(r'\/\d+', url_to_parse_hw[0]) # TODO re.findall c [0]
        inter_number = videos_number[0]

        url_to_parse_course = re.findall(r'study_groups/\d+/videos/', url) # TODO re.findall c [0]
        url_to_parse_course_number = re.findall(r'/\d+/', url_to_parse_course[0]) # TODO re.findall c [0]
        url_hw = url_to_parse_course_number[0]

        link_hw = f'{MAIN_URL}/study_groups' f'{url_hw}homeworks{inter_number}'
        return link_hw

class DownloadGB():
    """docstring for DownloadGB.

    """
    __was_downl_info = [
        ' Файл уже был скачен ранее , если скачен не корректно или не скачен \
(1. пропустить):',
        '1. удалите багованные файлы с компьютера',
        '2. и в начале использования скрипта введите цифру 2\n'
        ]
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
        if self.__html in content_type or self.__app_bin in content_type:
            return True
        return False

    def is_google_drive(self, _file_to_download):
        if self.__drive_google in _file_to_download or \
                self.__docs_google in _file_to_download:
            return True
        return False

    def main_download(self, courses, step):
        self.create_or_download(f'{MAIN_PATH}/')
        lessons = courses['lessons']
        chapters = courses['chapters']
        interactives = courses['interactives']
        courses = lessons + chapters + interactives
        for lesson in courses:
            _course_name, _lesson_name = self.replaces_for_paths(
                lesson['course_name'], lesson['lesson_name']
                )
            if step == 0 and lesson['is_downloaded']:
                print()
                print(f'{_lesson_name} ({lesson["content_url"]})')
                [print(i) for i in self.__was_downl_info]
                continue

            # create path
            self.create_or_download(f'{MAIN_PATH}/{_course_name}/')
            self.create_or_download(
                f'{MAIN_PATH}/{_course_name}/{_lesson_name}/'
                )

            # sonload info
            if lesson['comment'] is not None:
                self.create_or_download(
                    f'{MAIN_PATH}/{_course_name}/{_lesson_name}/{self.__attention}',
                    text=lesson['comment']
                    )
            if lesson['homework'] is not None:
                self.create_or_download(
                    f'{MAIN_PATH}/{_course_name}/{_lesson_name}/{self.__home_work}',
                    text=lesson['homework']
                    )

            _links_list = []
            _links_name_list = []
            _name_list = lesson['links']['name_list']
            _links_lists = lesson['links']['links_list']
            for n in _links_lists:
                _links_list.append(n)
            for n in _name_list:
                _links_name_list.append(n)
            _names = self.name_file(
                links_name_list=_links_name_list,
                links_list=_links_list
                )

            # TODO Если одинаковое название в списке с названием ссылок
            # для скачивания? Нужно сделать разные называния что бы
            # скачались, к примеру, оба видео, если были сбои
            n = 0
            while n+1 <= len(_links_list):
                self.create_or_download(
                f'{MAIN_PATH}/{_course_name}/{_lesson_name}/{_names[n]}',
                _file_to_download = _links_list[n],
                _pwd_path = f'{MAIN_PATH}/{_course_name}/{_lesson_name}'
                ),
                n += 1
            lesson['is_downloaded'] = True
        courses = {
            'lessons': lessons,
            'chapters': chapters,
            'interactives': interactives
            }
        write_to_json_file(JSON_COURSES_PATH, courses=courses)
        return courses

    def check_download_all(self, _file_to_download):
        try:
            request_url = requests.head(_file_to_download)
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

    def download_all(self, path, _file_to_download, _pwd_path):
        request_url, connection, content_type = self.check_download_all(
            _file_to_download
            )
        if request_url is not None:
            print(f"{_file_to_download} {self.__unexpexted_err}")
        if connection == 'close':
            print(f'{self.__acsses_err} {_file_to_download}')
        if content_type is None and self.is_web_url(content_type):
            if content_type is not None and self.is_google_drive(_file_to_download):
                print(f"{self.__google_sheet} {_file_to_download}")
            else:
                print(f"{self.__web_url} {_file_to_download}")
        else:
            urllib.request.urlretrieve(_file_to_download, path)
            print(f"{self.__download_file} {path}")
            return True

        return self.resave_urls_to_file(_file_to_download, _pwd_path)

    def create_or_download(self, path, _pwd_path=None, _file_to_download=None,
            text=None):
        if os.path.exists(f'{_pwd_path}/{self.__urls}'):
            print(f'{self.__arleady_exists} {_pwd_path}/{self.__urls}')
        if os.path.exists(path):
            print(f'{self.__arleady_exists} {path}')
        else:
            if _file_to_download is None and text is None:
                os.mkdir(path)
                print(f"{self.__create_path} {path}")
            elif text is not None:
                save_text_in_file(path, text)
                print(f"{self.__create_path} {path}")
            elif _file_to_download is not None:
                self.download_all(path, _file_to_download, _pwd_path)

    def resave_urls_to_file(self, file2download, pwd_path):
        path = f'{pwd_path}/{self.__urls}'
        lines = []
        if os.path.exists(path):
            lines = read_lines_from_file(path)
        lines.append(file2download)
        lines = set(lines)
        write_lines_in_file(path, lines)
        print(f'{self.__save_url_2_file} {path}')
        return True

    def replaces_for_paths(self, _course_name, _lesson_name):
        # заменяем все "\" и "/" на "_", что бы при скачивании порграмма
        # не считала, что это путь
        _course_name = _course_name.replace('\\', "_")
        _course_name = _course_name.replace("/", "_")
        _lesson_name = _lesson_name.replace('\\', "_")
        _lesson_name = _lesson_name.replace("/", "_")
        return _course_name, _lesson_name

    def name_file(self, links_name_list, links_list):
        n = 0
        names = []
        while n+1 <= len(links_list):
            if self.__docs_google in links_list[n] or \
                self.__drive_google in links_list[n]:
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
    __thanks = '\nСпасибо, за то, что воспользовались скриптом!\n'
    __offers = ('\nЖаль, что Вам не удлось воспользоваться скриптом.',
        "По вопросами и предложениям можно писать в Телеграм: @nishadrin \
        (https://t.me/nishadrin)\n")

    if main():
        print(__thanks)
    else:
        [print(i) for i in __offers]
