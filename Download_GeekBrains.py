#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json
import os
import urllib.request

import requests
from bs4 import BeautifulSoup


class ParseGB():
    """docstring for parse_GB

    """


    # инициируем авторизированную сессию
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.url = "https://geekbrains.ru/login"
        self.c = requests.Session()
        self.html = self.c.get(self.url,verify=True)
        self.soup = BeautifulSoup(self.html.content, "html.parser")
        self.hiddenAuthKey = self.soup.find(
            'input', {'name': 'authenticity_token'})['value']
        # authorization
        self.c.get(self.url,verify=True)
        self.login_data = {
            "utf8": "✓", "authenticity_token": self.hiddenAuthKey,
            "user[email]": self.email, "user[password]": self.password,
            "user[remember_me]": "0"
            }
        self.c.post("https://geekbrains.ru",
            data=self.login_data,
            headers={"Referer": "https://geekbrains.ru/login"}
            )

    # закрыть сессию
    def close_session(self):
        self.c.close()

    # Получаем ссылки на доступные уроки, вебинары, интерактивы
    def parse_courses(self):
        url_2_parse = "https://geekbrains.ru/education"
        filehtml = self.c.get(url_2_parse)
        soup_url_2_parse = BeautifulSoup(filehtml.content, "html.parser")
        temp_save_test = os.path.abspath('GeekBrains/test.html')
        info_url_2_parse = soup_url_2_parse.find(
            'script',
            {"data-component-name": "EducationPage"}
            ).text
        json_all_curses = json.loads(info_url_2_parse)
        webinars_and_interactives = json_all_curses['data']['lessons']
        videos = json_all_curses['data']['chapters']
        temp_file_save = os.path.abspath('GeekBrains/temp_file.json')
        interactives_urls = list()
        webinars_urls = list()
        videos_urls = list()
        for key, value in webinars_and_interactives.items():
            if "/study_groups/" in value['link']:
                interactives_urls.append(
                    f"https://geekbrains.ru{value['link']}/videos/{value['id']}"
                    )
            elif "/lessons/" in value['link']:
                webinars_urls.append(f"https://geekbrains.ru{value['link']}")

        for key, value in videos.items():
            videos_urls.append(f"https://geekbrains.ru{value['link']}")
        return webinars_urls, videos_urls, interactives_urls

    def parse_lesson_or_chapter(self, url):
        filehtml = self.c.get(url)
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
            filehtml_homework = self.c.get(url + "/homework")
            homework = BeautifulSoup(filehtml_homework.content, "html.parser")
            dz = homework.find("div", { "class" : "task-block-teacher" })
            if dz:
                dz = dz.text
            else:
                dz = None
        else:
            dz = None
        dic = {
            "course_name": course_name, "lesson_name": lesson_name,
            "content_url": url, "comment": comment, "links": links,
            "dz": dz
            }
        return dic

    def parse_interactive(self, url):
        filehtml = self.c.get(url)
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
        link_dz = 'https://geekbrains.ru/study_groups' + \
            f'{url_2_parse_course_number[0]}homeworks{videos_number[0]}'
        filehtml_hw = self.c.get(link_dz)
        soup_hw = BeautifulSoup(filehtml_hw.content, "html.parser")
        dz = soup_hw.find("div", {"class": "homework-description"}).text
        dic = {
            "course_name": course_name, "lesson_name": lesson_name,
            "content_url": url, "links": links, "dz": dz
            }
        return dic

class DownloadGB():
    """docstring for DownloadGB.

    """


    def download(self, path, file2download):
        request_url = requests.head(file2download)
        try:
            connection = request_url.headers['Connection']
        except Exception as e:
            connection = None
        if connection == 'close':
            print('Доступ к ресурсу запрещен')
            return 302
        try:
            content_type = request_url.headers['content-type']
        except Exception as e:
            content_type = None
        if "html" in content_type:
            if "docs.google.com" in file2download:
                print("google sheets еще не умею скачивать, " + \
                    "один файл не скачался"
                    )
            else:
                print("Скачать не могу, так как это ссылка на веб " + \
                    "страницу, а не на файл"
                    )
        else:
            urllib.request.urlretrieve(file2download, path)
            print(f"Скачали файл {path}")

    def create_or_download(self, path, file2download=None, text=None):
        if os.path.exists(path):
            print(f'Уже существует {path}')
        else:
            if file2download==None and text==None:
                os.mkdir(path)
                print(f"Создана папка {path}")

            elif text != None:
                with open(path, "w") as f:
                    f.write(text)
                print(f"Создан файл {path}")

            elif file2download != None:
                self.download(path, file2download)

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
    email = input('Введите email от GB: ')
    password = input('Введите пароль от GB: ')
    courses = os.path.abspath('courses.json')
    print(
        '\n1 - Пропарсить и сохранить в json',
        f'2 - Скачать из json (файл должен находится по пути: {courses})',
        '3 - Пропарсить и скачать (удаляется json файл)',
        '4-бесконечность - Пропарсить и скачать (сохранить json файл)\n',
        'PS: Для скачивания материала может потребоваться много времени ' +\
        'и места на жестком диске\n', sep='\n'
        )
    step = int(input('Что будем делать?(Введите цифру) '))
    if step != 2:
        lessons = None
        try:
            parse = ParseGB(email, password)
            lessons, chapters, interactives = parse.parse_courses()
        except Exception as e:
            lessons == None
        if lessons == None:
            print("\nНе удается скачать ссылки на уроки с основной страницы " +\
                "https://geekbrains.ru/education, возможные проблемы:",
                "1. Нет подключения к интернету",
                "2. Не верный логин и/или пароль от GB",
                "3. GB что то переделали на сайте, и надо редактировать скрипт",
                sep='\n'
                )
            return False
        else:
            print('Пропарсили страницу educations...')
        lessons_list = list()
        chapters_list = list()
        interactives_list = list()
        print('Парсим каждый урок по отдельности:')
        for i in lessons:
            print(f'Парсим ссылку {i}')
            dic = parse.parse_lesson_or_chapter(i)
            lessons_list.append(dic)
        for i in chapters:
            print(f'Парсим ссылку {i}')
            dic = parse.parse_lesson_or_chapter(i)
            chapters_list.append(dic)
        for i in interactives:
            print(f'Парсим ссылку {i}')
            dic = parse.parse_interactive(i)
            interactives_list.append(dic)
        # Сохраняем в файл json все данные по курсам
        list_json = {
            'lessons': lessons_list, 'chapters': chapters_list,
            'interactives': interactives_list
            }
        with open(courses, "w", encoding="utf-8") as file:
            file.write(json.dumps(list_json, ensure_ascii=False))
        print(f'Сохранили курсы в файл: {courses}')
    if step == 1:
        return True
    if step == 2:
        with open(courses, "r", encoding="utf-8") as file:
            read_json = json.load(file)
        lessons_list = read_json['lessons']
        chapters_list = read_json['chapters']
        interactives_list = read_json['interactives']
    print('Скачваем материал...')
    start_path = os.path.abspath('GeekBrains/')
    download = DownloadGB()
    download.create_or_download(path=start_path)
    for i in lessons_list+chapters_list+interactives_list:
        course_name = i['course_name']
        lesson_name = i['lesson_name']
        name_list = i['links']['name_list']
        links_lists = i['links']['links_list']
        # Заменяем все "\" и "/" на "_", что бы при скачивании порграмма
        #
        # не считала, что это путь
        course_name = re.sub(r'\\', "_", course_name)
        course_name = re.sub(r'/', "_", course_name)
        lesson_name = re.sub(r'\\', "_", lesson_name)
        lesson_name = re.sub(r'/', "_", lesson_name)
        # Создаем папки
        download.create_or_download(os.path.abspath('GeekBrains/'))
        download.create_or_download(os.path.abspath(
            f'GeekBrains/{course_name}/')
            )
        download.create_or_download(os.path.abspath(
            f'GeekBrains/{course_name}/{lesson_name}/')
            )
        # Скачаиваем инфу
        if i['comment'] != None:
            download.create_or_download(os.path.abspath(
                f'GeekBrains/{course_name}/{lesson_name}/Важные объявление.txt'),
                text= i['comment']
                )
        if i['dz'] != None:
            download.create_or_download(os.path.abspath(
                f'GeekBrains/{course_name}/{lesson_name}/Домашнее задание.txt'),
                text= i['dz']
                )
        links_list = list()
        for i in links_lists:
            links_list.append(i)
        links_name_list = list()
        for i in name_list:
            links_name_list.append(i)
        names = download.name_file(links_name_list, links_list)
        n = 0
        while n+1 <= len(links_list):
            download.create_or_download(os.path.abspath(
                f'GeekBrains/{course_name}/{lesson_name}/{names[n]}'),
                file2download = links_list[n]
                )
            n += 1
    parse.close_session()
    if step == 3:
        os.remove(courses)
    print('Спасибо, за использование скрипта!')

if __name__ == '__main__':
    main()
