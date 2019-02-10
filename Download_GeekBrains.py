# -*- coding: utf-8 -*-

import os
import urllib.request
import requests
from bs4 import BeautifulSoup
import re
"""
Посмотрите документацию к Классу (:

План:
1. Ввод данных от пользователя
    -Логин от GeekBrains
    -Пароль от GeekBrains
    #-Логин от Google
    #-Пароль от Google
2. Парсим сайты для работы, вытаскиваем данные
    -Ссылки всех открытых курсов
        -Ссылки (представлены в виде словаря, со списками ссылок на уроки, вебинары, интерактивы в виде цифр)
        -Урок №
        -Распределние
        ->далее из имеющихся тащим:
            -Названия
                #->-Урок №
            -Ссылки на материалы урока
            #-Важное объявление!
3. Создать папку куда скачивать, с проверкой на наличие папок и файлов, по всем путям что запарсили снова
4. Скачиваем файлы, которых нету
    #-Google shits
#5. Сделать проверку на обновления
#6. Используя tkinter сделать графическое приложени
#7. Google shits - загуглить (:
#8. Сравнивать вес файлов которые уже скачаннами, с теми, что есть на сервере: если разный, то удаляем файл, что есть и скачиваем новый
    -Можно уточнять у пользователя о замене файла скачивания, заменить или оставить
"""

class download_script():
    """Для удобного чтения свернуть все функции, приятного просмотра (:"""

    def create_path(self, path):

        if not os.path.exists(path):
            os.mkdir(path) # если нет пути, то создаем

    def download_file(self, file2download, path):
        if "google" in file2download:
            pass
        else:
            urllib.request.urlretrieve(file2download, path) # Скачиваем файл, если не гугл ссылка, file2download - ссылка на файл, который надо скачать, path - полный путь с именем куда скачать

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
            # get site's page and parse with regexp lessons's links
            url_2_parse = "https://geekbrains.ru/education"
            filehtml = c.get(url_2_parse).text
            webinar = re.findall('{"lessons":(\[[^\]]+\])', filehtml) # нужно переделать с lessons так как study_groups тоже имеет название курсов как и lessons
            video = re.findall('{"chapters":(\[[^\]]+\])', filehtml)
            interactive = re.findall('"\/study_groups\/(\d{1,})', filehtml)
            webinars = list()
            videos = list()
            interactives_all = list()
            interactives = list()
            for i in webinar:
                webinars.append(eval(i))
            for i in video:
                videos.append(eval(i))
            for i in interactive:
                interactives_all.append(eval(i))
                interactives = set(interactives_all)

            dic = {"webinars": webinars, "videos": videos, "interactives": interactives} # fix interactives Надо beautifullsoup'ом вытаскивать, так как в дessons входит еще и интерактив

            return dic # Получаем ссылки на уроки, вебинары, интерактивы, email и password от учетки Geekbrains # fix interactives inlessons

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
            # тащим из интерактива все, пока не знаю, что (:
            #Надо разобраться. Возможные ссылки:
            #https://geekbrains.ru/study_groups/5497/test
            #https://geekbrains.ru/study_groups/5497/videos/30188?tab=materials#materials
            #https://geekbrains.ru/study_groups/5497/videos/30188?tab=video#video
            #https://geekbrains.ru/study_groups/5497/homeworks/30187
            #https://geekbrains.ru/study_groups/5497/reviews/30187
            if "/study_groups" in url_2_parse:
                pass
            # тащим из урока номер урока с названием, материалы урока, важное объявление и ДЗ из ссылки+/homework
            else:
                filehtml = c.get(url_2_parse)
                soup = BeautifulSoup(filehtml.content, "html.parser")
                """ Для скачивания html страницы (анализ)
                filehtml_text = c.get(url_2_parse).text
                with open("/home/nick/Документы/Программирование/Свое/Скачать все с GeekBrains/GeekBrains/file.html", "w") as f:
                    f.write(filehtml_text)
                """
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
                    dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "links": links}

                    return dic

                else:
                    # тащим ДЗ к вебинару и название вебинара
                    if "/lessons" in url_2_parse:
                        filehtml_homework = c.get(url_2_parse+"/homework")
                        homework = BeautifulSoup(filehtml_homework.content, "html.parser")
                        dz = homework.find("div", { "class" : "task-block-teacher" }).text # Тащим ДЗ
                        lesson_name = homework.find("div", { "class" : "title-block" }).text # Тащим название вебинара
                        dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "comment": comment, "links": links, "dz": dz}

                        return dic

                dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "comment": comment, "links": links}

                return dic # Парсинг страниц работает вроде корректно, если поправить webinar в get_parse_lessons()


def test(email, password, url_2_parse):
    url = "https://geekbrains.ru/login"
    with requests.Session() as c:
        html = c.get(url,verify=True)
        soup = BeautifulSoup(html.content, "html.parser")
        hiddenAuthKey = soup.find('input', {'name': 'authenticity_token'})['value']
        # authorization
        c.get(url,verify=True)
        login_data = {"utf8": "✓", "authenticity_token": hiddenAuthKey, "user[email]": email, "user[password]": password, "user[remember_me]": "0"}
        c.post("https://geekbrains.ru/wanna_captcha", data=login_data, headers={"Referer": "https://geekbrains.ru/login"})

        filehtml = c.get(url_2_parse)
        soup_url_2_parse = BeautifulSoup(filehtml.content, "html.parser")
        info_url_2_parse = soup_url_2_parse.find('script', {"data-component-name": "EducationPage"}).text

        print(info_url_2_parse)


def main():
    # Ввод данных
    email = 'geekbrains@mail.com'
    password = 'passwd'
    download = download_script()
    # Парсим все ссылки на уроки, вебинары и интерактивы
    #curs_dic = download.get_parse_lessons(email, password)
    #test = download.get_parse_materials(email, password, "https://geekbrains.ru/education")
    """
    lesson_info = {}
    lessons_info = {}
    for i in curs_dic["videos"]:
        for j in i:
            all_curse_info = download.get_parse_materials(email, password, f"https://geekbrains.ru/chapters/{j}")
            lesson_info[f"{all_curse_info['lesson_name']}"] = all_curse_info
            print(f'\n{lesson_info}\n')
        lessons_info[f"{all_curse_info['curse_name']}"] = lesson_info
        print("\nВесь вебинар\n")
        print(f'{lessons_info}\n')
    """

    test(email, password, "https://geekbrains.ru/education")

    #"https://geekbrains.ru/lessons/32489/homework"
    #"https://geekbrains.ru/lessons/32489"
    #https://geekbrains.ru/chapters/2008

if __name__ == '__main__':
    main()
