import vk_api
import configparser
import argparse
from utils import two_factor_handler
import pandas as pd
from tqdm import tqdm
from multiprocessing import Pool

# parser = argparse.ArgumentParser(description='User VK-account parser')
# parser.add_argument('--config', type=str, default='config-example.ini', help='Name of config-file')
# args = parser.parse_args()
#
# config = configparser.ConfigParser()
# config.read(args.config)

# login = config.get('vk', 'login', fallback=None)
#
# if login is None or len(login) < 1:
#     print("No login in the config-file")
#
# password = config.get('vk', 'password', fallback=None)
#
# if password is None or len(password) < 1:
#     print("No password in the config-file")


features = {
    "about": "Содержимое поля «О себе» из профиля",
    "activities": "Содержимое поля «Деятельность» из профиля",
    "bdate": "Дата рождения. Возвращается в формате D.M.YYYY или D.M (если год рождения скрыт)."
             "Если дата рождения скрыта целиком, поле отсутствует в ответе",
    "books": "Содержимое поля «Любимые книги» из профиля пользователя",
    "can_post": "Информация о том, можно ли оставлять записи на стене",
    "can_see_all_posts": "Информация о том, можно ли видеть чужие записи на стене",
    "can_see_audio": "Информация о том, можно ли видеть аудиозаписи",
    "can_send_friend_request": "Информация о том, будет ли отправлено уведомление пользователю о заявке в друзья",
    "can_write_private_message": "",
    "career": "Информация о карьере пользователя",
    "city": "Информация о городе, указанном на странице пользователя в разделе «Контакты»",
    "connections": "Данные об указанных в профиле сервисах пользователя, таких как:"
                   "skype, facebook, twitter, livejournal, instagram",
    "contacts": "Информация о телефонных номерах пользователя",
    "counters": {
        "albums": "Количество фотоальбомов",
        "videos": "Количество видеозаписей",
        "audios": "Количество аудиозаписей",
        "photos": "Количество фотографий",
        "notes": "Количество заметок",
        "friends": "Количество друзей",
        "groups": "Количество сообществ",
        "online_friends": "Количество друзей онлайн",
        "user_videos": "Количество видеозаписей с пользователем",
        "followers": "Количество подписчиков",
        "pages": "Количество объектов в блоке «Интересные страницы»",
        "subscriptions": "Количество подписок",
        "clips_followers": "Количество подписчиков на клипы",
    },
    "country": "Информация о стране, указанной на странице пользователя",
    "crop_photo": "Информация, вырезана ли профильная и миниатюрная фотографии пользователя, при наличии",
    "domain": "Короткий адрес страницы",
    "education": "Информация о высшем учебном заведении пользователя",
    "exports": "",
    "followers_count": "Количество подписчиков пользователя",
    "games": "Содержимое поля «Любимые игры» из профиля",
    "has_mobile": "Информация о том, известен ли номер мобильного телефона пользователя",
    "has_photo": "Информация о том, установил ли пользователь фотографию для профиля",
    "home_town": "Название родного города",
    "interests": "Содержимое поля «Интересы» из профиля",
    "last_seen": "Тип платформы последнего посещения",
    "movies": "Содержимое поля «Любимые фильмы»",
    "music": "Содержимое поля «Любимая музыка»",
    "nickname": "Никнейм (отчество) пользователя",
    "occupation": "Информация о текущем роде занятия пользователя",
    "personal": {
        "political": "Политические предпочтения",
        "langs": "Языки",
        "religion": "Мировоззрение",
        "inspired_by": "Источники вдохновения",
        "people_main": "Главное в людях",
        "life_main": "Главное в жизни",
        "smoking": "Отношение к курению",
        "alcohol": "Отношение к алкоголю"
    },
    "quotes": "Любимые цитаты",
    "relatives": "Список родственников",
    "relation": "Семейное положение",
    "schools": "Список школ, в которых учился пользователь",
    "screen_name": "Короткое имя страницы",
    "sex": "Пол",
    "site": "Адрес сайта, указанный в профиле",
    "status": "Статус пользователя",
    "tv": "Любимые телешоу",
    "universities": "Список вузов, в которых учился пользователь",
    "verified": "Информация верифицирована ли страница пользователя"
}
# Составляем список полей, которые запрашиваем о пользователе
fields = ','.join(features.keys())


def parse(data):
    token, user = data
    # Создаем объект сессии VK
    vk_session = vk_api.VkApi(
        token=token,
        api_version="5.122")

    # Получаем VK API
    vk = vk_session.get_api()

    answer = []

    for info in vk.users.get(user_ids=user, fields=fields):

        ID: int = info['id']  # идентификатор пользователя
        first_name: str = info['first_name']  # имя
        last_name: str = info['last_name']  # фамилия
        is_closed: int = int(info.get('is_closed')) if info.get(
            'is_closed') is not None else -1  # скрыт ли профиль пользователя настройками приватности
        deactivated: bool = True if info.get('deactivated') is not None else False  # содержит значение deleted или banned
        about: bool = True if info.get('about') is not None and len(
            info.get('about')) != 0 else False  # содержимое поля «О себе» из профиля
        activities: bool = True if info.get('activities') is not None and len(
            info.get('activities')) != 0 else False  # содержимое поля «Деятельность» из профиля
        bdate: bool = True if info.get(
            'bdate') is not None else False  # дата рождения. Возвращается в формате D.M.YYYY или D.M (если год рождения скрыт)
        books: bool = True if info.get('books') is not None and len(
            info.get('books')) != 0 else False  # содержимое поля «Любимые книги» из профиля пользователя
        can_post: int = info.get('can_post')  # информация о том, может ли текущий пользователь оставлять записи на стене
        # 0 - не может | 1 - может
        can_see_all_posts: int = info.get('can_see_all_posts', -1)  # информация о том, может ли текущий пользователь
        # видеть чужие записи на стене
        # 0 - не может | 1 - может
        can_see_audio: int = info.get('can_see_audio',
                                      -1)  # информация о том, может ли текущий пользователь видеть аудиозаписи
        # 0 - не может | 1 - может
        can_send_friend_request: int = info.get('can_send_friend_request', -1)  # информация о том, будет ли отправлено
        # уведомление пользователю о заявке в друзья
        # от текущего пользователя
        # 1 — уведомление будет отправлено
        # 0 — уведомление не будет отправлено
        can_write_private_message: int = info.get('can_write_private_message', -1)  # информация о том, может ли текущий
        # пользователь отправить личное сообщение
        # 0 - не может | 1 - может

        career: bool = True if info.get('career') is not None and len(
            info.get('career')) != 0 else False  # информация о карьере пользователя
        city: bool = True if info.get('city') is not None and len(info.get('city')) != 0 else False  # информация о городе
        connections: bool = True if info.get('connections') is not None and len(
            info.get('connections')) != 0 else False  # информация об указанных в профиле
        # сервисах пользователя
        contacts: bool = True if info.get('contacts') is not None and len(
            info.get('contacts')) != 0 else False  # информация о телефонных номерах

        counters = info.get('counters', {})

        counters_albums: int = counters.get('albums', -1)
        counters_videos: int = counters.get('videos', -1)
        counters_audios: int = counters.get('audios', -1)
        counters_photos: int = counters.get('photos', -1)
        counters_notes: int = counters.get('notes', -1)
        counters_friends: int = counters.get('friends', -1)
        counters_groups: int = counters.get('groups', -1)
        counters_user_videos: int = counters.get('user_videos', -1)
        counters_followers: int = counters.get('followers', -1)
        counters_pages: int = counters.get('pages', -1)

        country: bool = True if info.get('country') is not None and len(info.get('country')) != 0 else False

        crop_photo: bool = False
        crop = info.get('crop_photo', {}).get('crop', {'x': 0.0, 'y': 0.0, 'x2': 100.0, 'y2': 100.0})
        if crop['x'] != 0.0 or crop['y'] != 0.0 or crop['x2'] != 100.0 or crop['y2'] != 100.0:
            crop_photo = True

        domain: str = info.get('domain')
        education: bool = True if info.get('education') is not None else False
        followers_count: int = info.get('followers_count', -1)

        games: bool = True if info.get('games') is not None and len(info.get('games')) != 0 else False
        has_mobile: int = info.get('has_mobile', -1)  # номер телефона
        # 1 — известен, 0 — не известен
        has_photo: int = info.get('has_photo', -1)  # 1, если пользователь установил фотографию для профиля
        home_town: str = True if info.get('home_town') is not None and len(
            info.get('home_town')) != 0 else False  # название родного города
        interests: str = True if info.get('interests') is not None and len(
            info.get('interests')) != 0 else False  # содержимое поля «Интересы» из профиля
        last_seen_platform: bool = True if info.get('last_seen', {}).get('platform') is not None else False
        military: bool = True if info.get('military') is not None else False
        movies: bool = True if info.get('movies') is not None and len(info.get('movies')) != 0 else False
        music: bool = True if info.get('music') is not None and len(info.get('music')) != 0 else False
        occupation: bool = True if info.get('occupation') is not None else False

        personal = info.get('personal', {})
        personal_political: int = personal.get('political', -1)  # политические предпочтения
        personal_langs: bool = True if personal.get('langs') is not None and len(
            personal.get('langs')) != 0 else False  # языки
        personal_religion: str = True if personal.get('religion') is not None and len(
            personal.get('religion')) != 0 else False  # мировоззрение
        personal_inspired_by: str = True if personal.get('personal_inspired_by') is not None and len(
            personal.get('personal_inspired_by')) != 0 else False  # источники вдохновения
        personal_people_main: int = personal.get('people_main', -1)  # главное в людях
        personal_life_main: int = personal.get('life_main', -1)  # главное в жизни
        personal_smoking: int = personal.get('smoking', -1)  # отношение к курению
        personal_alcohol: int = personal.get('alcohol', -1)  # отношение к алкоголю

        quotes: str = True if info.get('quotes') is not None and len(info.get('quotes')) != 0 else False  # любимые цитаты

        relatives: bool = True if info.get('relatives') is not None and len(info.get('relatives')) != 0 else False

        relation: int = info.get('relation', -1)

        schools: bool = True if info.get('schools') is not None and len(info.get('schools')) != 0 else False

        sex: int = info.get('sex', -1)

        status: str = True if info.get('status') is not None and len(info.get('status')) != 0 else False

        tv: str = True if info.get('tv') is not None and len(info.get('tv')) != 0 else False

        universities: bool = True if info.get('universities') is not None and len(info.get('universities')) != 0 else False

        verified: int = info.get('verified', -1)

        # составляем список фич
        all_features = {
            "ID": ID,
            "first_name": first_name,
            "last_name": last_name,
            "is_closed": is_closed,
            "deactivated": deactivated,
            "about": about,
            "activities": activities,
            "bdate": bdate,
            "books": books,
            "can_post": can_post,
            "can_see_all_posts": can_see_all_posts,
            "can_see_audio": can_see_audio,
            "can_send_friend_request": can_send_friend_request,
            "can_write_private_message": can_write_private_message,
            "career": career,
            "city": city,
            "connections": connections,
            "contacts": contacts,
            "counters_albums": counters_albums,
            "counters_videos": counters_videos,
            "counters_audios": counters_audios,
            "counters_photos": counters_photos,
            "counters_notes": counters_notes,
            "counters_friends": counters_friends,
            "counters_groups": counters_groups,
            "counters_user_videos": counters_user_videos,
            "counters_followers": counters_followers,
            "counters_pages": counters_pages,
            "country": country,
            "crop_photo": crop_photo,
            "domain": domain,
            "education": education,
            "followers_count": followers_count,
            "games": games,
            "has_mobile": has_mobile,
            "has_photo": has_photo,
            "home_town": home_town,
            "interests": interests,
            "last_seen_platform": last_seen_platform,
            "military": military,
            "movies": movies,
            "music": music,
            "occupation": occupation,
            "personal_political": personal_political,
            "personal_langs": personal_langs,
            "personal_religion": personal_religion,
            "personal_inspired_by": personal_inspired_by,
            "personal_people_main": personal_people_main,
            "personal_life_main": personal_life_main,
            "personal_smoking": personal_smoking,
            "personal_alcohol": personal_alcohol,
            "quotes": quotes,
            "relatives": relatives,
            "relation": relation,
            "schools": schools,
            "sex": sex,
            "status": status,
            "tv": tv,
            "universities": universities,
            "verified": verified
        }

        answer.append(all_features)

    return answer
