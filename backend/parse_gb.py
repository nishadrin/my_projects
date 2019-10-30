import re
import json

import requests
from bs4 import BeautifulSoup
from pprint import pprint

import secrets
from config import *
# TODO name_list пустые строки и одинаковых названий
def start_parse():
    """Run all processes and return json file with all info and urls
    or None.

    """
    login = AuthorizationGB()
    session = login.connect()
    if session is None:
        login.disconnect(session)
        return None
    courses_info = session.parse()
    login.disconnect(session)
    return courses_info



class AuthorizationGB():
    """Authorization to use class ParseGB().
    To authorization, use connect().
    To unauthorization, use disconnect(session).

    """


    def disconnect(self, session):
        return session.close_session() if session is not None else None

    def connect(self):
        # email, password = self.login() # TODO
        email, password = secrets.email, secrets.password # TODO
        return self.authorization(email, password)

    def login(self):
        email = input('Введите email от GB: ')
        password = input('Введите пароль от GB: ')
        return email, password

    def authorization(self, email, password):
        try:
            authorization = ParseGB(email, password)
        except Exception as AuthorizationError:
            authorization = None
        if authorization is None:
            [print(error) for error in ERROR_MESSAGES]
            return None
        return authorization


class ParseGB():
    """Parse site https://geekbrains.ru/education for information
    about all courses witch you buy.
    Parse lesson, chapter and interactive, but last one
    without videos. Return json file with all info and urls or None.

    Parse info in everyone lesson (if it exists):
    1. course info
    2. course materials, including video
    3. homework info
    4. important information

    """


    __save_in_file = 'Сохранили в файл:'
    __parse_one_lesson = 'Парсим каждый урок по отдельности:'
    __parse_educ_url = 'Парсим страницу educations...'
    __parse_educ_url_err = f'Не удалось пропарсить страницу {COURSES_URL}'
    __parse_url = 'Парсим ссылку'
    __parse_vid_web_err = 'Не удалось пропарсить видео/вебинары'
    __parse_inter_err = 'Не удалось пропарсить страницу интерактивы'

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
        return True


    def get_soup(self, url):
        try:
            html = self.connect.get(url)
            print(html)
        except Exception as e:
            return None
        return BeautifulSoup(html.content, "html.parser")

    def create_urls_inter(self, courses, ):
        courses_list = []
        for course in courses:
            url = f"{MAIN_URL}{courses[0]}/{course}"
            courses_list.append(url)
        return courses_list

    def create_urls_less_or_chap(self, urls, is_chapters):
        course_list = []
        for url in urls:
            if is_chapters:
                url = f"{MAIN_URL}/chapters/{url}"
            else:
                url = f"{MAIN_URL}/lessons/{url}"
            course_list.append(url)
        return course_list

    def create_urls_interactives(self, num, urls):
        course_list = [] # https://geekbrains.ru/study_groups/5497/videos/30188
        for url in urls:
            url_course = f"{MAIN_URL}/study_groups/{num}/videos/{url}/"
            url_hw = f"{MAIN_URL}/study_groups/{num}/homeworks/{url}/"
            urls_with_hw = {
                'url': url_course,
                'url_hw': url_hw
                }
            course_list.append(urls_with_hw)
        return course_list


    def parse(self):
        courses = self.parse_courses()
        if courses is None:
            return None
        lessons = self.parse_less_or_chap(courses['lessons'])
        chapters = self.parse_less_or_chap(
            courses['chapters'],
            is_chapters=True
            )
        interactives = self.parse_interactives(courses['interactives'])
        return {
            'lessons': lessons, 'chapters': chapters,
            'interactives': interactives
            }

    def parse_courses(self):
        courses = self.get_courses()
        lessons_dict, chapters_dict, interactives_dict = {}, {}, {},
        for num, course in courses.items():
            if course['state'] == 'require_courses':
                continue

            if course['courseType'] == 'basic':
                try:
                    lessons = course['progressItems']['lessons']
                except Exception as e:
                    lessons = None
                if lessons is not None:
                    lessons_dict[num] = lessons
            if course['courseType'] == 'video':
                try:
                    chapters = course['progressItems']['chapters']
                except Exception as e:
                    chapters = None
                if chapters is not None:
                    chapters_dict[num] = chapters
            if course['courseType'] == 'interactive':
                try:
                    lessons = course['progressItems']['lessons']
                except Exception as e:
                    lessons = None
                if lessons is not None:
                    interactive_link = re.search(
                        r'\d+',
                        course['link']
                        )
                    interactives_dict[interactive_link.group()] = lessons
        if lessons is None and chapters is None and interactives_dict is None:
            return None
        return {
            'lessons': lessons_dict,
            'chapters': chapters_dict,
            'interactives': interactives_dict
            }

    def get_courses(self):
        soup_courses = self.get_soup(COURSES_URL)
        # try:
        #    find_courses = soup_courses.find(
        #         'script', {"data-component-name": "EducationPage"}
        #         ).text
        # except Exception as EducationParseError:
        #     return None
        find_courses = soup_courses.find(
            'script', {"data-component-name": "EducationPage"}
            ).text
        if find_courses is None:
            return None
        loads = json.loads(find_courses)
        return loads['data']['attendees']

    def parse_less_or_chap(self, courses, is_chapters=False):
        lesson_dict = {}
        for num, course in courses.items():
            lessons_urls = self.create_urls_less_or_chap(
                course, is_chapters=is_chapters
                )
            lesson_dict[num] = self.get_less_or_chap(
                lessons_urls, is_chapters=is_chapters
                )
        return lesson_dict

    def get_less_or_chap(self, urls, is_chapters):
        lessons_info = []
        for url in urls:
            parse_lesson = self.parse_one_less_or_chap(
                url, is_chapters=is_chapters
                )
            lessons_info.append(parse_lesson)
        return lessons_info

    def parse_one_less_or_chap(self, url, is_chapters):
        links_list, name_list = [], []
        lesson_soup = self.get_soup(url)
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
        if not is_chapters:
            homework_soup = self.get_soup(f'{url}/homework')
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

    def parse_interactives(self, interactives):
        lesson_dict = {}
        for num, course in interactives.items():
            print(course)
            lessons_urls = self.create_urls_interactives(num, course)
            lesson_dict[num] = self.get_interactives(lessons_urls)
        return lesson_dict

    def get_interactives(self, urls):
        lessons_info = []
        for url in urls:
            print(url)
            parse_lesson = self.parse_interactive(url['url'], url['url_hw'])
            lessons_info.append(parse_lesson)
        return lessons_info

    def parse_interactive(self, url, url_hw):
        interactive_soup = self.get_soup(url)
        hw_soup = self.get_soup(url_hw)

        links_list, name_list = [], []
        for i in interactive_soup.findAll("div", {"class": "lesson-contents"}):
            links_list.append(i.find("a")['href'])
            name_list.append(i.find("a").text)

        homework = hw_soup.find("div", {"class": "homework-description"}).text
        course_name = interactive_soup.find(
            "span",
            {"class": "course-title"}
            ).text
        lesson_name = interactive_soup.find("h3", {"class": "title"}).text
        links = {"name_list": name_list, "links_list": links_list}
        return {
            "course_name": course_name, "lesson_name": lesson_name,
            "content_url": url, "links": links, "comment": None,
            "homework": homework, "is_downloaded": False
            }


if __name__ == '__main__':
    pprint(start_parse())
