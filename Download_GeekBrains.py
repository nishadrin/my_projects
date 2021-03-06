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
            'script', {"data-component-name": "EducationPage"}
            ).text
        json_all_curses = json.loads(info_url_2_parse)
        webinars_and_interactives = json_all_curses['data']['lessons']
        videos = json_all_curses['data']['chapters']
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
        is_downloaded = False
        dic = {
            "course_name": course_name, "lesson_name": lesson_name,
            "content_url": url, "comment": comment, "links": links,
            "dz": dz, "is_downloaded": is_downloaded
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

    def download(self, path, file2download, pwd_path):
        try:
            request_url = requests.head(file2download)
        except Exception as e:
            request_url = None
        if request_url == None :
            print(f"{file2download} cкачать не могу, по непонятным причинам")
            self.save_urls(file2download, pwd_path)
            return False
        try:
            connection = request_url.headers['Connection']
        except Exception as e:
            connection = None
        if connection == 'close':
            print(f'Доступ к ресурсу {file2download} запрещен')
            self.save_urls(file2download, pwd_path)
            return False
        try:
            content_type = request_url.headers['content-type']
        except Exception as e:
            content_type = None
        if content_type == None or "html" in content_type or \
                'application/binary' in content_type:
            if content_type != None and "drive.google.com" in file2download \
                    or "docs.google.com" in file2download:
                print("Скачать не могу, так как это ссылка на google sheets " + \
                    f"страницу: {file2download}"
                    )
                self.save_urls(file2download, pwd_path)
            else:
                print("Скачать не могу, так как это ссылка на веб " + \
                    f"страницу: {file2download}"
                    )
                self.save_urls(file2download, pwd_path)
        else:
            urllib.request.urlretrieve(file2download, path)
            print(f"Скачали файл {path}")

    def create_or_download(self, path, pwd_path=None, file2download=None, text=None):
        if os.path.exists(path):
            print(f'Уже существует {path}')
        elif os.path.exists(f'{pwd_path}/Ссылки.txt'):
            print(f'Уже существует {pwd_path}/Ссылки.txt')
        else:
            if file2download==None and text==None:
                os.mkdir(path)
                print(f"Создана папка {path}")

            elif text != None:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                print(f"Создан файл {path}")

            elif file2download != None:
                self.download(path, file2download, pwd_path)

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
    courses = os.path.abspath('courses.json')
    main_menu = [
        '1 - Пропарсить и сохранить в json',
        f'2 - Скачать из json (файл должен находится по пути: {courses})',
        '3 - Пропарсить и скачать (удаляется json файл)',
        '>4 - Пропарсить и скачать (сохранить json файл)\n',
        'PS: Для скачивания материала может потребоваться много времени ' +\
        'и места на жестком диске\n',
        ]
    error_message = [
        "\nНе удается скачать ссылки на уроки с основной страницы " +\
        "https://geekbrains.ru/education, возможные проблемы:",
        "1. Нет подключения к интернету",
        "2. Не верный логин и/или пароль от GB",
        "3. GB что то переделали на сайте, и надо редактировать скрипт",
        ]
    if os.path.exists(courses):
        main_menu.insert(0, "0 - Продолжить скачивать",)
    print('*' * 50)
    for i in main_menu:
        print(i)
    step = int(input('Что будем делать?(Введите цифру) '))
    if step != 2 and step != 0:
        print('*' * 50)
        email = input('Введите email от GB: ')
        password = input('Введите пароль от GB: ')
        print('*' * 50)
        try:
            parse = ParseGB(email, password)
            lessons, chapters, interactives = parse.parse_courses()
        except Exception as e:
            lessons = None
        if lessons == None:
            for i in error_message:
                print(i)
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
        parse.close_session()
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
    if step == 2 or step == 0:
        if not os.path.exists(courses):
            print(f'\nНе вижу файл: {courses}')
            return False
        with open(courses, "r", encoding="utf-8") as file:
            read_json = json.load(file)
        lessons_list = read_json['lessons']
        chapters_list = read_json['chapters']
        interactives_list = read_json['interactives']
    print('Скачваем материал...')
    download = DownloadGB()
    download.create_or_download(os.path.abspath('GeekBrains/'))
    for i in lessons_list+chapters_list+interactives_list:
        print('*' * 50)
        course_name = i['course_name']
        lesson_name = i['lesson_name']
        name_list = i['links']['name_list']
        links_lists = i['links']['links_list']
        # заменяем все "\" и "/" на "_", что бы при скачивании порграмма
        # не считала, что это путь
        course_name = re.sub(r'\\', "_", course_name)
        course_name = re.sub(r'/', "_", course_name)
        lesson_name = re.sub(r'\\', "_", lesson_name)
        lesson_name = re.sub(r'/', "_", lesson_name)
        # продолжить скачивание (0)
        if step == 0 and i['is_downloaded']:
            way_path = f'GeekBrains/{course_name}/{lesson_name}/'
            downloaded_message = (
                f'Курс {i["content_url"]} уже был скачен ранее, если ' + \
                'скачен не корректно или не скачен (1 шаг пропустить):',
                f'1. удалите файлы с компьютера по пути: {way_path}',
                '2. и в начале использования скрипта введите цифру 2'
                )
            print('*' * 50)
            for i in downloaded_message:
                print(i)
            continue
        # создаем папки
        download.create_or_download(os.path.abspath(
            f'GeekBrains/{course_name}/')
            )
        download.create_or_download(os.path.abspath(
            f'GeekBrains/{course_name}/{lesson_name}/')
            )
        # скачаиваем инфу
        if i['comment'] != None:
            download.create_or_download(os.path.abspath(
                f'GeekBrains/{course_name}/{lesson_name}/Важные объявление.txt'),
                text=i['comment']
                )
        if i['dz'] != None:
            download.create_or_download(os.path.abspath(
                f'GeekBrains/{course_name}/{lesson_name}/Домашнее задание.txt'),
                text=i['dz']
                )
        links_list = list()
        for n in links_lists:
            links_list.append(n)
        links_name_list = list()
        for n in name_list:
            links_name_list.append(n)
        names = download.name_file(links_name_list, links_list)
        n = 0
        while n+1 <= len(links_list):
            download.create_or_download(
                os.path.abspath(
                    f'GeekBrains/{course_name}/{lesson_name}/{names[n]}'
                    ),
                file2download = links_list[n],
                pwd_path = os.path.abspath(
                    f'GeekBrains/{course_name}/{lesson_name}'
                    )
                )
            n += 1
        i['is_downloaded'] = True
    list_save = {
        'lessons': lessons_list,
        'chapters': chapters_list,
        'interactives': interactives_list
        }
    with open(courses, "w", encoding="utf-8") as file:
        file.write(json.dumps(list_save, ensure_ascii=False))
    if step == 3:
        os.remove(courses)
    return True

if __name__ == '__main__':
    if main():
        print('Спасибо, за то, что воспользовались скриптом!')
    else:
        print('\nЖаль, что Вам не удлось воспользоваться скриптом.',
            "По вопросами и предложениям можно писать в Телеграм: @nishadrin" +\
            "(https://t.me/nishadrin)", sep='\n')
