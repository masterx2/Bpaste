#!/usr/bin/env python
# -*- encoding: UTF-8 -*-

import ConfigParser
from subprocess import Popen, PIPE
from sys import stdin, getsizeof
from os import getenv, error, path
from urllib import urlencode, urlopen

# Русский разговорник для [argparse]
# нужно проинить до импорта либы
import gettext
gettext.gettext = lambda string: {
    'usage: ': 'юзание: ',
    'positional arguments': 'позиционные аргументы',
    'optional arguments': 'Всякие доп. аргументы кудаж без них',
    'show this help message and exit': 'Показать этот хелп и умереть'
}[string]

import argparse

# Тут всякие глобальные настройки
config_file_path = getenv('HOME') + '/.bpasterc'


class Paster:
    """PasteBin.com PiPe Paster

Эта незатейливая утилита отправляет ввод с STDIN на
http://pastebin.com, и по умолчанию в качестве имени
фрагмента использует цепочку вызовов пайпа текущей
команды шелла, не то что бы я уверен что именно так
и произойдёт), но задумка была именно такая."""

    def __init__(self, apikey):
        """Подготовка к старту"""

        self.userKey = ''
        self.format = 'Python'
        self.apiUrl = 'http://pastebin.com/api/api_post.php'
        self.loginUrl = 'http://pastebin.com/api/api_login.php'

        # Читаем конфиг если есть
        config = ConfigParser.ConfigParser()

        if path.exists(config_file_path):
            try:
                config.read(config_file_path)
                self.apiKey = config.get('user', 'api_key')
                self.userName = config.get('user', 'user')
                self.userPassword = config.get('user', 'password')
                self.userKey = config.get('user', 'user_key')
            except Exception as e:
                print 'Ошибка чтения конфига =('
                print e
                if self.userKey == '' :
                    if not self.userName and not self.userPassword:
                        print "Нужно в конфиге прописать имя и пароль от Pastebin"
                        quit()
                    else:
                        self.userKey = self.login(self.userName, self.userPassword)
                        config.set('user', 'user_key', self.userKey)
                        with open(config_file_path, 'wb') as cf:
                            config.write(cf)
        else:
            print 'Без конфига нихера не получится! =( пока...'
            quit()

    @staticmethod
    def request(params, url):
        """Запрос к API серверу Pastebin.com.

        :param params:
        :param url:

        Note:
            Метод не проверяет полученные данные и не обрабатывает ошибки API.
            Патамушта!
            Ой, всё!

        Args:
            url (str): За какую урлу дергаем API-сервер.
            params (dict): Именованный массив параметров для отправки методом POST.

        Returns:
            result (str): Строку с результатами или False в случае неудачи.

        """
        try:
            result = urlopen(url, urlencode(params)).read()
        except error.URLError:
            result = False

        return result

    def login(self, username, password):
        """Получение api_user_key.

        Args:
            username: Логин от Pastebin.com
            password: Пароль от Pastebin.com

        Attributes:
            self.user_key (str): Содержит api_user_key при успешном получении ответа.

        """
        params = {
            'api_dev_key': self.apiKey,
            'api_user_name': username,
            'api_user_password': password,
        }

        return self.request(params, self.loginUrl)

    @staticmethod
    def getstdin():
        """Получение данных из STDIN.

        Note:
            Pastebin.com установил лимит на фрагменты в 500 килобайт, метод
            проверяет размер полученных данных, привысив лимит он прекращает
            читать stdin и возвращает false.

        Returns:
            out (str):

        """
        # TODO 'шечка Влепить прогрессбар процесса.. c байтами и строками

        out = ''
        for line in stdin:
            out += line + '/n'
            if getsizeof(out, 0) > 5e5:
                raise Exception("Ноу-ноу-ноу слишком большой фрагмент. Не влезет в Pastebin.com")

        return out

    def send(self, title, data):
        """Формировка и отправка запроса на размещение фрагмента

        Note:
            Основной метод.

        Args:

        """
        params = {
            'api_dev_key': self.apiKey,
            'api_user_key': self.userKey,
            'api_option': 'paste',
            'api_paste_name': title,
            'api_paste_expire_date': '10M',
            'api_paste_format': self.format,
            'api_paste_code': data,
            'api_paste_private': '1'  # Unlisted by Default
        }

        return self.request(params, self.apiUrl)

    @staticmethod
    def getcommand():
        """Метод который получает строку запуска последней команды текущего шелла

        Note:
            Эта хрень работает только на ZSH

        Returns:
            (str): Возвращает цепочку вызовов со всеми параметрами кроме последнего элемента.

        """
        line = Popen("tail -1 $HOME/.zsh_history | cut -d';' -f2-", shell=True, stdout=PIPE, stderr=PIPE).stdout.read()
        return '|'.join(line.split('|')[:-1])


def main():
    # Разбор аргуметов
    ap = argparse.ArgumentParser(description=Paster.__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument('-v', '--verbose', action='store_true', help="Режим говорливости")
    ap.add_argument('-e', '--echo', action='store_true', help="Дублировать вывод в консоль")
    ap.add_argument('-t', '--type', action='store_true', help="Тип фрагмента: public, unlisted(по-умолчанию), private")
    ap.add_argument('-f', '--format', action='store_true', help="Синтаксит фрагмента, по-умолчанию None")
    ap.add_argument('-c', '--command', action='store_true', help="Показать пайп вызова и умереть")
    ap.add_argument('-i', '--init-config', action='store_true',
                    help="Создать/перезаписать конфиг в %%HOME/.bpasterc")
    ap.add_argument('-g', '--guest', action='store_true', help="Игнорировать аутификацию")
    ap.add_argument('--userkey', action='store', help="[api_user_key] от Pastebin.com, если конечно он у тебя есть")
    ap.add_argument('--user', action='store', help="Логин Pastebin.com")
    ap.add_argument('--password', action='store', help="Пароль Pastebin.com")
    ap.add_argument('--apikey', action='store', help="Свой собственный API-key к Pastebin.com\nвместо встоенного")
    args = ap.parse_args()

    # Погнали
    # Иним Пастер
    paster = Paster('36996dc288496021c5d3b9ca2c5b8f2f')

    # Дебажные опции
    if args.command:
        print paster.getcommand()
        quit()

    # Получаем stdin
    pipe = paster.getstdin()
    # Получем команду
    command = paster.getcommand()

    if pipe != "":
        print paster.send(command, pipe)

    else:
        # Ничего не пришло
        # А может и не должно было?
        if command == '':
            # Или ты баран запустил скрипт просто так
            # или случилось что-то страшное
            # Будем считать что ты Баран =)
            print 'Baran Mode On'
        else:
            # Команда есть, данных нет
            print 'Bad Times'
            print command

if __name__ == '__main__':
    main()