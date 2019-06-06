#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib.request
from bs4 import BeautifulSoup
import re, json, time, random, os, requests
import googleapiclient


class parse_GB():
    """docstring for parse_GB"""
    # инициируем авторизированную сессию
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.url = "https://geekbrains.ru/login"
        self.c = requests.Session()
        self.html = self.c.get(self.url,verify=True)
        self.soup = BeautifulSoup(self.html.content, "html.parser")
        self.hiddenAuthKey = self.soup.find('input', {'name': 'authenticity_token'})['value']
        # authorization
        self.c.get(self.url,verify=True)
        self.login_data = {"utf8": "✓", "authenticity_token": self.hiddenAuthKey, "user[email]": self.email, "user[password]": self.password, "user[remember_me]": "0"}
        self.c.post("https://geekbrains.ru/wanna_captcha", data=self.login_data, headers={"Referer": "https://geekbrains.ru/login"})
    # закрыть сессию
    def close_session(self):
        self.c.close()
    # Получаем ссылки на доступные уроки, вебинары, интерактивы, email и password от учетки Geekbrains
    def get_parse_lessons(self):
        # get site's page and parse with json
        url_2_parse = "https://geekbrains.ru/education"
        filehtml = self.c.get(url_2_parse)
        soup_url_2_parse = BeautifulSoup(filehtml.content, "html.parser")
        info_url_2_parse = soup_url_2_parse.find('script', {"data-component-name": "EducationPage"}).text
        json_all_curses = json.loads(info_url_2_parse)
        webinars_and_interactives = json_all_curses['data']['lessons']
        video = json_all_curses['data']['chapters']
        interactives = list()
        webinars = list()
        videos = list()
        temp_file_save = os.path.abspath('GeekBrains/temp_file.json')

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

        for i in urls_list:
            self.add_dic_2_json(i, temp_file_save)

        return urls_list
    #Добавление словаря в файл
    def add_dic_2_json(self, dic, path):
        list_json = list()

        if not os.path.exists(path):
            list_json.append(dic)

            with open(path, "w", encoding="utf-8") as file:
                file.write(json.dumps(list_json, ensure_ascii=False))

        else:
            with open(path, "r", encoding="utf-8") as file:
                read_json = json.load(file)
                for i in read_json:
                    list_json.append(i)

                if dic not in list_json:
                    list_json.append(dic)

            with open(path, "w", encoding="utf-8") as file:
                file.write(json.dumps(list_json, ensure_ascii=False))
    # Парсинг страниц на наличие материала в уроках url_2_parse - ссылка для парсинга # Умеет работать с /study_groups, /lessons, /chapters
    def get_parse_materials(self, url_2_parse):
        path = os.path.abspath('GeekBrains/save_lesson_info.json')
        # стараемся избежать ошибки Connection broken вызываемое GB
        # time.sleep(random.randint(30, 60))
        # парсим из интерактива, видео работант через api, пока не парсим (:
        print("\nСслыка, которую парсим: ", url_2_parse)
        filehtml = self.c.get(url_2_parse)
        soup = BeautifulSoup(filehtml.content, "html.parser")
        links_list = list()
        name_list = list()

        if "/study_groups" in url_2_parse:

            for i in soup.findAll("div", {"class": "lesson-contents"}):
                links_list.append(i.find("a")['href'])
                name_list.append(i.find("a").text)

            links = {"name_list": name_list, "links_list": links_list}
            curse_name = soup.find("span", {"class": "course-title"}).text
            lesson_name = soup.find("div", {"class": "main-header__left"}).text

            url_2_parse_hw = re.findall(r'\/videos\/\d+', url_2_parse)
            videos_number = re.findall(r'\/\d+', url_2_parse_hw[0])

            url_2_parse_curs = re.findall(r'study_groups/\d+/videos/', url_2_parse)
            url_2_parse_curs_number = re.findall(r'/\d+/', url_2_parse_curs[0])

            link_dz = f'https://geekbrains.ru/study_groups{url_2_parse_curs_number[0]}homeworks{videos_number[0]}'
            print(link_dz)
            filehtml_hw = self.c.get(link_dz)
            soup_hw = BeautifulSoup(filehtml_hw.content, "html.parser")
            dz = soup_hw.find("div", {"class": "homework-description"}).text

            dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "links": links, "dz": dz}

            self.add_dic_2_json(dic, path)

            return dic
        # парсим из урока номер урока с названием, материалы урока, важное объявление и ДЗ из ссылки+/homework
        else:
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
                    filehtml_homework = self.c.get(url_2_parse+"/homework")
                    homework = BeautifulSoup(filehtml_homework.content, "html.parser")
                    try:
                        dz = homework.find("div", { "class" : "task-block-teacher" }).text # парсим ДЗ
                    except Exception as e:
                        dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "links": links}

                        self.add_dic_2_json(dic, path)

                        return dic

                    else:
                        lesson_name = homework.find("div", { "class" : "title-block" }).text # парсим название вебинара

                        dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "links": links, "dz": dz}

                        self.add_dic_2_json(dic, path)

                        return dic

                dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "links": links}

                self.add_dic_2_json(dic, path)

                return dic

            else:
                if "/lessons" in url_2_parse:
                    filehtml_homework = self.c.get(url_2_parse+"/homework")
                    homework = BeautifulSoup(filehtml_homework.content, "html.parser")
                    try:
                        dz = homework.find("div", { "class" : "task-block-teacher" }).text # парсим ДЗ
                    except Exception as e:
                        dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "comment": comment, "links": links}

                        self.add_dic_2_json(dic, path)

                        return dic

                    else:
                        lesson_name = homework.find("div", { "class" : "title-block" }).text # парсим название вебинара

                        dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "comment": comment, "links": links, "dz": dz}

                        self.add_dic_2_json(dic, path)

                        return dic

                dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse,"comment": comment, "links": links}

                self.add_dic_2_json(dic, path)

                return dic

            dic = {"curse_name": curse_name, "lesson_name": lesson_name, "content_url": url_2_parse, "comment": comment, "links": links}

            self.add_dic_2_json(dic, path)

            return dic
    # Парсинг материала с сохранением в файл ссылок, которые не пропарсились
    def save_parsing(self, file_list_with_urls):
        save_lost = os.path.abspath('GeekBrains/save_lost.json')

        with open(file_list_with_urls, "r+", encoding="utf-8") as f:
            read_json = json.load(f)
            for i in read_json:
                try:
                    self.get_parse_materials(i)
                    # read_json.remove(i)
                except Exception as e:
                    self.add_dic_2_json(i, save_lost)
                    # read_json.remove(i)
                    print("\nЧасть ссылок не удалось пропарсить, ищите список тут: " + save_lost)

class work_with_disk():
    """docstring for work_with_disk."""
    # Запрос логина и пароля от GB
    def input_acc(self):
        email = input("Введите Ваш E-mail от GeekBrains: ")
        passwd = input("Введите Ваш пароль от GeekBrains: ")
        dic = {"email": email, "passwd": passwd}
        return dic
    # Создаем папку/файл или просто скачиваем с интернета, path - полный путь с именем куда скачать, file2download(необязательный) - ссылка на файл, который надо скачать, text(необязательный) - текст который должен записаться в файл
    def download_file(self, path, file2download=None, text=None):
        save_parsing_sites = os.path.abspath('cant_download.json')
        if not os.path.exists(path):
            if file2download==None and text==None:
                os.mkdir(path)
                print(f"Создана папка {path}\n")

            elif text != None:
                with open(path, "w") as f:
                    f.write(text)
                print(f"Создан файл {path}\n")

            elif file2download != None:
                try:
                    check_file_or_link = requests.head(file2download)
                except Exception as e:
                    pass
                else:
                    try:
                        if "html" in check_file_or_link.headers['content-type']:
                            if ".google.com" in file2download:

                                print("google sheets еще не умею скачивать, один файл не скачался\n")
                            else:
                                print("Скачать не могу, так как это ссылка на веб страницу, а не на файл")
                        else:
                            try:
                                urllib.request.urlretrieve(file2download, path)
                                print(f"Скачали файл {path}\n")
                            except Exception as e:
                                print("Не удалось разобраться со станицей: " + file2download)

                    except Exception as e:
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

def main():
    disk_work = work_with_disk()

    email_passwd_dic = disk_work.input_acc()
    email = email_passwd_dic["email"]
    password = email_passwd_dic["passwd"]

    try:
        parse_links = parse_GB(email, password)
    except Exception as e:
        print("Не удается скачать ссылки на уроки с основной страницы https://geekbrains.ru/education, возможные проблемы:\nНет подключения к интернетуНе верный логин и/или пароль от GB")

    start_path = os.path.abspath('GeekBrains/')

    disk_work.download_file(path=start_path)

    path_save_lesson = os.path.abspath('GeekBrains/save_lesson_info.json')
    temp_file_save = os.path.abspath('GeekBrains/temp_file.json')
    save_lost = os.path.abspath('GeekBrains/save_lost.json')

    # Парсим ссылки на уроки
    try:
        parse_lesson = parse_links.get_parse_lessons()
    except Exception as e:
        print("\nНе удается скачать ссылки на уроки с основной страницы https://geekbrains.ru/education, возможные проблемы:\nНе верный логин и/или пароль от GB\nСервер GB не в рабочем состоянии, либо там что то изменилось.")


    # Парсим каждый урок, и парсим, все что не удалось ранее пропарсить
    parse_links.save_parsing(temp_file_save)

    if os.path.exists(save_lost):
        print("Есть уроки, где материал не получалось пропарсить, попробуем еще раз")
        parse_links.save_parsing(save_lost)

    # Скачиваем материал
    print("Начинаем скачивать материал, который удалось пропарсить, это может занять длительное время, зависит от скорости соединения с серверами")

    with open(path_save_lesson, "r", encoding="utf-8") as f:
        path_save_lesson_json = json.load(f)

        for i in path_save_lesson_json:
            curse_name = i['curse_name']
            lesson_name = i['lesson_name']
            name_list = i['links']['name_list']
            links_lists = i['links']['links_list']
            # Заменяем все "\" и "/" на "_", что бы при скачивании порграмма не считала, что это путь
            curse_name = re.sub(r'\\', "_", curse_name)
            curse_name = re.sub(r'/', "_", curse_name)
            lesson_name = re.sub(r'\\', "_", lesson_name)
            lesson_name = re.sub(r'/', "_", lesson_name)
            # Создаем папки
            disk_work.download_file(os.path.abspath('GeekBrains/'))
            disk_work.download_file(os.path.abspath(f'GeekBrains/{curse_name}/'))
            disk_work.download_file(os.path.abspath(f'GeekBrains/{curse_name}/{lesson_name}/'))
            # Скачаиваем инфу
            try:
                disk_work.download_file(os.path.abspath(f'GeekBrains/{curse_name}/{lesson_name}/Важные объявление.txt'), text= i['comment'])
            except Exception as e:
                pass

            try:
                disk_work.download_file(os.path.abspath(f'GeekBrains/{curse_name}/{lesson_name}/Домашнее задание.txt'), text = i['dz'])
            except Exception as e:
                pass

            links_list = list()
            for i in links_lists:
                links_list.append(i)

            links_name_list = list()
            for i in name_list:
                links_name_list.append(i)

            names = disk_work.name_file(links_name_list, links_list)

            n = 0
            while n+1 <= len(links_list):
                disk_work.download_file(os.path.abspath(f'GeekBrains/{curse_name}/{lesson_name}/{names[n]}'), file2download = links_list[n])
                n += 1

    # Зкрываем сессию
    parse_links.close_session()

    # Удаляем временные файлы
    os.remove(path_save_lesson)
    os.remove(temp_file_save)

    # Окончание
    if os.path.exists(save_lost):
        print("\nНе удалось скачать некоторые курсы, ищите список тут: " + save_lost)
    else:
        print("Спасибо, что воспольовались скриптом!")

if __name__ == '__main__':
    main()
