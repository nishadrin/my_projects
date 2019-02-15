#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import urllib.request
import requests
from bs4 import BeautifulSoup
import re
import json
import pprint
"""
План:
1. Ввод данных от пользователя
    #-Логин от Google
    #-Пароль от Google
#2. Скачиваем файлы, которых нету
    #-Google shits
#3. Google shits - загуглить (:
#4. Используя tkinter сделать графическое приложени
#5. Сделать проверку на обновления и отправку отчетов об ошибке
#6. Сравнивать размер файла которые уже скачаный, с теми, что есть на сервере: если разный размер, то удаляем файл, что есть и скачиваем новый
    -Можно уточнять у пользователя о замене файла скачивания, заменить или оставить
#7. Оптимизировать код
"""

class download_script():
    """Скачиваем все доступные уроки, комменты, дз с GeekBrains"""
    # Получаем ссылки на доступные уроки, вебинары, интерактивы, email и password от учетки Geekbrains
    def get_parse_lessons(self, email, password):
        url = "https://geekbrains.ru/login"
        with requests.Session() as c:
            html = c.get(url,verify=True)
            soup = BeautifulSoup(html.content, "html.parser")
            hiddenAuthKey = soup.find('input', {'name': 'authenticity_token'})['value']
            # authorization
            c.get(url,verify=True)
            login_data = {"utf8": "✓", "authenticity_token": hiddenAuthKey, "user[email]": email, "user[password]": password, "user[remember_me]": "0"}
            c.post("https://geekbrains.ru/wanna_captcha", data=login_data, headers={"Referer": "https://geekbrains.ru/login"})
            # get site's page and parse with json
            url_2_parse = "https://geekbrains.ru/education"
            filehtml = c.get(url_2_parse)
            soup_url_2_parse = BeautifulSoup(filehtml.content, "html.parser")
            info_url_2_parse = soup_url_2_parse.find('script', {"data-component-name": "EducationPage"}).text
            json_all_curses = json.loads(info_url_2_parse)
            webinars_and_interactives = json_all_curses['data']['lessons']
            video = json_all_curses['data']['chapters']
            interactives = list()
            webinars = list()
            videos = list()
            for key, value in webinars_and_interactives.items():
                if "/study_groups/" in value['link']:
                    interactives.append(value)

                elif "/lessons/" in value['link']:
                    webinars.append(value)

            for key, value in video.items():
                videos.append(value)

            dic = {"webinars": webinars, "videos": videos, "interactives": interactives}

            urls_list = list()
            for i in dic['webinars']:
                link = i['link']
                urls_list.append(f'https://geekbrains.ru{link}')

            for i in dic['videos']:
                link = i['link']
                urls_list.append(f'https://geekbrains.ru{link}')

            for i in dic['interactives']:
                link = i['link']
                study_groups = i['id']
                urls_list.append(f'https://geekbrains.ru{link}/videos/{study_groups}')

            return urls_list
    # Парсинг страниц на наличие материала в уроках url_2_parse - ссылка для парсинга # Умеет работать с /study_groups, /lessons, /chapters
    def get_parse_materials(self, email, password, url_2_parse):
        url = "https://geekbrains.ru/login"

        with requests.Session() as c:
            html = c.get(url,verify=True)
            soup = BeautifulSoup(html.content, "html.parser")
            hiddenAuthKey = soup.find('input', {'name': 'authenticity_token'})['value']
            # authorization
            c.get(url,verify=True)
            login_data = {"utf8": "✓", "authenticity_token": hiddenAuthKey, "user[email]": email, "user[password]": password, "user[remember_me]": "0"}
            c.post("https://geekbrains.ru/wanna_captcha", data=login_data, headers={"Referer": "https://geekbrains.ru/login"})
            # тащим из интерактива, видео работант через api, пока не тащим (:
            if "/study_groups" in url_2_parse:
                filehtml = c.get(url_2_parse)
                soup = BeautifulSoup(filehtml.content, "html.parser")

                links_list = list()
                name_list = list()
                for i in soup.findAll("div", {"class": "lesson-contents"}):
                    links_list.append(i.find("a")['href'])
                    name_list.append(i.find("a").text)

                links = {"name_list": name_list, "links_list": links_list}
                curse_name = soup.find("span", {"class": "course-title"}).text
                lesson_name = soup.find("div", {"class": "main-header__left"}).text

                url_2_parse_hw = re.findall(r'\/videos\/\d+', url_2_parse)
                videos_number = re.findall(r'\/\d+', url_2_parse_hw[0])
                link_dz = f'https://geekbrains.ru/study_groups/5497/homeworks{videos_number[0]}'

                filehtml_hw = c.get(link_dz)
                soup_hw = BeautifulSoup(filehtml_hw.content, "html.parser")
                dz = soup_hw.find("div", {"class": "homework-description"}).text

                dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "links": links, "dz": dz}

                return dic
            # тащим из урока номер урока с названием, материалы урока, важное объявление и ДЗ из ссылки+/homework
            else:
                filehtml = c.get(url_2_parse)
                soup = BeautifulSoup(filehtml.content, "html.parser")
                links_list = list()
                name_list = list()
                for i in soup.findAll("li", {"class": "lesson-contents__list-item"}):
                    links_list.append(i.find("a")['href'])
                    name_list.append(i.find("a").text)

                links = {"name_list": name_list, "links_list": links_list}
                curse_name = soup.find("span", {"class": "course-title"}).text
                lesson_name = soup.find("div", {"class": "title-block"}).text
                try:
                    comment = soup.find("div", {"class": "lesson-content__content"}).text
                except Exception as e:
                    if "/lessons" in url_2_parse:
                        filehtml_homework = c.get(url_2_parse+"/homework")
                        homework = BeautifulSoup(filehtml_homework.content, "html.parser")
                        try:
                            dz = homework.find("div", { "class" : "task-block-teacher" }).text # Тащим ДЗ
                        except Exception as e:
                            dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "links": links}
                        else:
                            lesson_name = homework.find("div", { "class" : "title-block" }).text # Тащим название вебинара

                            dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "links": links, "dz": dz}

                            return dic

                    dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "links": links}

                    return dic

                else:
                    if "/lessons" in url_2_parse:
                        filehtml_homework = c.get(url_2_parse+"/homework")
                        homework = BeautifulSoup(filehtml_homework.content, "html.parser")
                        try:
                            dz = homework.find("div", { "class" : "task-block-teacher" }).text # Тащим ДЗ
                        except Exception as e:
                            dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "comment": comment, "links": links}
                        else:
                            lesson_name = homework.find("div", { "class" : "title-block" }).text # Тащим название вебинара

                            dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "comment": comment, "links": links, "dz": dz}

                            return dic

                    dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse,"comment": comment, "links": links}

                    return dic

                dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "comment": comment, "links": links}

                return dic
    # Создаем папку/файл или просто скачиваем с интернета, path - полный путь с именем куда скачать, file2download(необязательный) - ссылка на файл, который надо скачать, text(необязательный) - текст который должен записаться в файл
    def download_file(self, path, file2download=None, text=None):
        if not os.path.exists(path):
            if file2download==None and text==None:
                os.mkdir(path)
                print(f"Создана папка {path}\n")

            elif text != None:
                with open(path, "w") as f:
                    f.write(text)
                print(f"Создан файл {path}\n")

            elif file2download !=  None:
                if ".google.com" in file2download:
                    pass
                else:
                    urllib.request.urlretrieve(file2download, path)
                    print(f"Скачали файл {path}\n")
        else:
            print(f"Путь/файл {path} уже существует\n")
    # Создаем имена с расширениями скачевыемых файлов
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

def fixit(email, password, url_2_parse):
    pass

def main():
    # Ввод данных
    email = 'geekbrains@mail.com'
    password = 'passwd'
    download = download_script()

    # Парсим все ссылки на уроки, вебинары и интерактивы
    urls_list = download.get_parse_lessons(email, password)

    for i in urls_list:
        # Парсим сайт
        materials = download.get_parse_materials(email, password, i)
        curse_name = materials['curse_name']
        #print(f'{curse_name}\n')
        lesson_name = materials['lesson_name']
        name_list = materials['links']['name_list']
        links_lists = materials['links']['links_list']
        # Заменяем все "\" и "/" на "_", что бы при скачивании порграмма не считала, что это путь
        curse_name = re.sub(r'\\', "_", curse_name)
        curse_name = re.sub(r'/', "_", curse_name)
        lesson_name = re.sub(r'\\', "_", lesson_name)
        lesson_name = re.sub(r'/', "_", lesson_name)
        # Создаем папки
        download.download_file(os.path.abspath('GeekBrains/'))
        download.download_file(os.path.abspath(f'GeekBrains/{curse_name}/'))
        download.download_file(os.path.abspath(f'GeekBrains/{curse_name}/{lesson_name}/'))
        # Скачаиваем инфу
        try:
            download.download_file(os.path.abspath(f'GeekBrains/{curse_name}/{lesson_name}/Важные объявление.txt'), text= materials['comment'])
        except Exception as e:
            pass

        try:
            download.download_file(os.path.abspath(f'GeekBrains/{curse_name}/{lesson_name}/Домашнее задание.txt'), text = materials['dz'])
        except Exception as e:
            pass

        links_list = list()
        for i in links_lists:
            links_list.append(i)

        links_name_list = list()
        for i in name_list:
            links_name_list.append(i)

        names = download.name_file(links_name_list, links_list)

        n = 0
        while n+1 <= len(links_list):
            download.download_file(os.path.abspath(f'GeekBrains/{curse_name}/{lesson_name}/{names[n]}'), file2download = links_list[n])
            n += 1

if __name__ == '__main__':
    main()
