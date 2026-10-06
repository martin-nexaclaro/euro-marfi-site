from __future__ import annotations

import io
import json
import os
import re
import uuid
from html import unescape
from html.parser import HTMLParser
from copy import deepcopy
from datetime import datetime ,time ,timedelta
from pathlib import Path
from urllib.error import HTTPError ,URLError
from urllib.parse import quote
from urllib.request import Request ,urlopen
from xml.sax.saxutils import escape as xml_escape

try :
    from zoneinfo import ZoneInfo ,ZoneInfoNotFoundError
except ImportError :
    ZoneInfo =None
    ZoneInfoNotFoundError =Exception

import pyotp
import qrcode
from flask import Flask ,Response ,flash ,redirect ,render_template ,request ,session ,url_for
from qrcode .image .svg import SvgPathImage
from werkzeug.security import check_password_hash ,generate_password_hash
from werkzeug.utils import secure_filename

app =Flask (__name__ )
app .config ["SECRET_KEY"]=os .environ .get ("SECRET_KEY","change-this-secret-key-before-production")
app .config ["PREFERRED_URL_SCHEME"]="https"
app .config ["PERMANENT_SESSION_LIFETIME"]=timedelta (days =30 )
app .config ["SESSION_COOKIE_HTTPONLY"]=True
app .config ["SESSION_COOKIE_SAMESITE"]="Lax"

# Change this starter username later for the real owner/admin login.
# The password is now stored as a secure hash in data/admin_settings.json
# and can be changed from inside the admin panel.
ADMIN_USERNAME ="admin"
ADMIN_PASSWORD ="changeme123"

BASE_DIR =Path (__file__ ).resolve ().parent
DATA_FILE =BASE_DIR /"data"/"site_data.json"
ADMIN_SETTINGS_FILE =BASE_DIR /"data"/"admin_settings.json"
LIVE_RATES_CACHE_FILE =BASE_DIR /"data"/"live_rates_cache.json"
GALLERY_DIR =BASE_DIR /"static"/"images"/"gallery"
VIDEO_DIR =BASE_DIR /"static"/"videos"
DEFAULT_SITE_URL ="https://menuvacnica.com.mk"
LIVE_RATES_SOURCE_URL =os .environ .get ("LIVE_RATES_SOURCE_URL","https://www.menuvacnica.mk/").strip ()
LIVE_RATES_TIMEOUT =float (os .environ .get ("LIVE_RATES_TIMEOUT","4")or 4)
LIVE_RATES_CACHE_SECONDS =int (os .environ .get ("LIVE_RATES_CACHE_SECONDS","300")or 300)
LEGACY_SITE_URLS ={"https://menuvacnica.mk","http://menuvacnica.mk"}
LEGACY_SITE_HOSTS ={"menuvacnica.mk","www.menuvacnica.mk"}
SUPPORTED_LANGUAGES =("mk","en")
_GALLERY_ALLOWED_EXTENSIONS ={"jpg","jpeg","png","webp","gif"}
_VIDEO_ALLOWED_EXTENSIONS ={"mp4","webm","mov","avi","mkv"}
SUPABASE_URL =os .environ .get ("SUPABASE_URL","").strip ().rstrip ("/")
SUPABASE_KEY =(
os .environ .get ("SUPABASE_SERVICE_ROLE_KEY","" ).strip ()
or os .environ .get ("SUPABASE_ANON_KEY","").strip ()
)
SUPABASE_TABLE =os .environ .get ("SUPABASE_TABLE","site_settings" ).strip ()or "site_settings"
SUPABASE_STORAGE_BUCKET =os .environ .get ("SUPABASE_STORAGE_BUCKET","site-media" ).strip ()
SUPABASE_MEDIA_PREFIX =os .environ .get ("SUPABASE_MEDIA_PREFIX","uploads" ).strip ("/")
SUPABASE_TIMEOUT =float (os .environ .get ("SUPABASE_TIMEOUT","8" )or 8)
LEGACY_VISITOR_COUNT =2991516
PUBLIC_SITEMAP_PAGES =(
("index","weekly","1.0"),
("kursna_lista","daily","0.95"),
("menuvacnica_skopje","weekly","0.9"),
("menuvacnici_skopje","weekly","0.9"),
("lokacija","monthly","0.8"),
("galerija","monthly","0.7"),
)
CANONICAL_ENDPOINTS ={
"en_index":"index",
"en_kursna_lista":"kursna_lista",
"en_exchange_office_skopje":"menuvacnica_skopje",
"en_exchange_offices_skopje":"menuvacnici_skopje",
"en_lokacija":"lokacija",
"en_galerija":"galerija",
}
LOCALIZED_ROUTE_PATHS ={
"index":{"mk":"/","en":"/en/"},
"kursna_lista":{"mk":"/kursna-lista","en":"/en/exchange-rates"},
"menuvacnica_skopje":{"mk":"/menuvacnica-skopje","en":"/en/exchange-office-skopje"},
"menuvacnici_skopje":{"mk":"/menuvacnici-skopje","en":"/en/exchange-offices-skopje"},
"lokacija":{"mk":"/lokacija","en":"/en/location"},
"galerija":{"mk":"/galerija","en":"/en/gallery"},
}
SEO_HOME_TITLE ={
"mk":"Курсна Листа - Менувачница ЕУРО МАРФИ Скопје",
"en":"Exchange Rates - EURO MARFI Exchange Office Skopje",
}
SEO_HOME_DESCRIPTION ={
"mk":"ЕУРО МАРФИ е менувачница во Скопје со дневна курсна листа, куповен и продажен курс за EUR, USD, GBP, CHF и други валути.",
"en":"EURO MARFI is an exchange office in Skopje with daily buy and sell exchange rates for EUR, USD, GBP, CHF and other currencies.",
}
SEO_GALLERY_DESCRIPTION ={
"mk":"Фотографии од менувачницата ЕУРО МАРФИ, локацијата, ентериерот и услугата за менување девизи во Скопје.",
"en":"Photos of EURO MARFI exchange office, location, interior, and foreign currency exchange service in Skopje.",
}
SEO_IMAGE_FILENAME ="images/gallery/menuva5.jpg"
NOINDEX_ENDPOINTS ={"login","admin","logout","set_language"}

try :
    SKOPJE_TZ =ZoneInfo ("Europe/Skopje")if ZoneInfo else None
except ZoneInfoNotFoundError :
# Fallback for Windows/dev environments where tzdata is not installed.
    SKOPJE_TZ =None

UI_TEXT ={
"mk":{
"nav_home":"Почетна",
"nav_location":"Локација",
"nav_gallery":"Галерија",
"nav_admin":"Админ",
"nav_menu":"Мени",
"brand_open":"Отворено",
"brand_closed":"Затворено",
"hero_eyebrow":"Курсна листа",
"hero_title":"Дневен курс на девизи, веднаш видлив за секој посетител.",
"stat_currencies":"Валути",
"stat_currencies_text":"Главни валути прикажани веднаш при отворање на страната",
"stat_contact":"Контакт",
"stat_contact_value":"Брзо",
"stat_contact_text":"Телефони за повик, локација и дневни информации на едно место",
"badge_label":"Информации",
"badge_value":"ЕУРО МАРФИ",
"badge_title":"Дневен курс",
"badge_text":"Прегледна и практична поставеност за брза проверка на курсеви и контакт со менувачницата.",
"chip_hours":"Работно време",
"chip_hours_value":"Видливо",
"chip_notes":"Забелешки",
"chip_notes_value":"Ажурирачки",
"rates_eyebrow":"Курсна листа",
"rates_title":"Курсна листа",
"rates_text":"Курсната листа е најважниот дел од почетната страница и останува лесна за читање и на компјутер и на мобилен.",
"rates_card_title":"Куповен / Продажен курс",
"hours_label":"Работно време:",
"rates_card_text":"Преглед на дневните курсеви за посетителите",
"table_currency":"Валута",
"table_buy":"Куповен",
"table_sell":"Продажен",
"notes_eyebrow":"Забелешки",
"notes_title":"Известувања",
"notes_text":"Кратки и практични известувања под курсната листа за поважни информации во текот на денот.",
"contact_eyebrow":"Контакт",
"contact_title":"Јавете се директно",
"contact_text":"Брз контакт за проверка на курс, информации и услуга.",
"faq_eyebrow":"Прашања",
"faq_title":"Чести прашања за курсна листа",
"faq_items":[
{"question":"Каде има менувачница во Скопје?","answer":"ЕУРО МАРФИ се наоѓа на ul. Hristo Tatarchev 33a, Skopje 1000. На страницата Локација има мапа, адреса и директен телефонски контакт."},
{"question":"Кога се ажурира курсната листа?","answer":"Курсната листа се проверува и ажурира секој ден од сопственикот со најновите куповни и продажни курсеви."},
{"question":"Кои валути се прикажани на курсната листа?","answer":"На страницата се прикажани куповен и продажен курс за EUR, USD, GBP, CHF, CAD, AUD, RSD, BGN, TRY и ALB. За други валути, јавете ни се директно."},
],
"call_label":"Јавете се",
"moneygram_title":"MoneyGram трансфер услуги",
"moneygram_text":"Во менувачницата е достапна и услуга за MoneyGram парични трансфери.",
"location_eyebrow":"Локација",
"location_title":"Посетете нè",
"location_link":"Отвори локација",
"counter_eyebrow":"Посетители",
"counter_text":"Бројач на посетители на веб-страната.",
"location_page_title":"Локација",
"address_label":"Адреса",
"location_page_eyebrow":"Контакт и насока",
"location_page_text":"Прегледна страница со адреса, директен телефонски контакт и мапа за полесно пронаоѓање на менувачницата.",
"location_exact_address":"Точна адреса",
"location_visit_title":"Посетете ја менувачницата",
"location_visit_text":"Ова е главната деловна адреса прикажана на страницата и во контакт секцијата.",
"map_title":"Мапа за локација",
"gallery_page_title":"Галерија",
"gallery_page_eyebrow":"Нашата менувачница",
"gallery_page_text":"Галерија подготвена за фотографии од менувачницата, внатрешноста и услугата, со истата модерна визуелна насока.",
"gallery_source":"Извор на слики",
"gallery_source_text":"Локални датотеки во static/images",
"gallery_item":"Слика",
"footer_text":"Доверлива менувачница од 2007 година",
"footer_rights":"Сите права се задржани",
"lang_label":"Јазик",
"currency_default_name":"Валута",
"viber_label":"Пиши ни на Viber",
"whatsapp_label":"Пиши ни на WhatsApp",
"contact_dock_label":"Контакт опции",
"gallery_prev_label":"Претходна фотографија",
"gallery_next_label":"Следна фотографија",
"gallery_navigation_label":"Навигација низ галерија",
"gallery_show_photo_label":"Прикажи фотографија",
"login_page_title":"Админ најава",
"login_title":"Админ најава",
"login_owner_only":"Само за сопственикот",
"username_label":"Корисничко име",
"password_label":"Лозинка",
"login_submit":"Најави се",
"admin_page_title":"Админ панел",
"admin_kicker":"Контролен панел",
"admin_title":"Уредување на содржина",
"admin_subtitle_text":"Пополнете ги полињата и зачувајте. Јавните страници поддржуваат македонска и англиска верзија, а курсевите остануваат заеднички.",
"admin_preview":"Преглед на сајт",
"admin_logout":"Одјава",
"admin_basic_title":"Основни податоци",
"admin_basic_text":"Содржина за почетна и локација",
"admin_daily_info_mk":"Дневна информација MK",
"admin_daily_info_en":"Дневна информација EN",
"admin_working_hours_mk":"Работно време MK",
"admin_working_hours_en":"Работно време EN",
"admin_phone_1":"Телефон 1",
"admin_phone_2":"Телефон 2",
"admin_address":"Адреса",
"admin_map_link":"Линк за мапа",
"admin_notes_title":"Забелешки под курсна листа",
"admin_notes_text":"Одделни текстови за MK и EN",
"admin_note_1_mk":"Забелешка 1 MK",
"admin_note_1_en":"Забелешка 1 EN",
"admin_note_2_mk":"Забелешка 2 MK",
"admin_note_2_en":"Забелешка 2 EN",
"admin_note_3_mk":"Забелешка 3 MK",
"admin_note_3_en":"Забелешка 3 EN",
"admin_rates_title":"Курсна листа",
"admin_rates_text":"Сите постоечки валути остануваат уредливи",
"admin_flag_label":"Ознака на знаме",
"admin_buy_label":"Куповен курс",
"admin_sell_label":"Продажен курс",
"admin_save_changes":"Зачувај промени",
},
"en":{
"nav_home":"Home",
"nav_location":"Location",
"nav_gallery":"Gallery",
"nav_admin":"Admin",
"nav_menu":"Menu",
"brand_open":"Open",
"brand_closed":"Closed",
"hero_eyebrow":"Exchange Rates",
"hero_title":"Daily exchange rates, visible immediately for every visitor.",
"stat_currencies":"Currencies",
"stat_currencies_text":"Main currencies shown immediately when the page opens",
"stat_contact":"Contact",
"stat_contact_value":"Direct",
"stat_contact_text":"Tap-to-call numbers, location access, and daily information in one place",
"badge_label":"Information",
"badge_value":"EURO MARFI",
"badge_title":"Daily Rates",
"badge_text":"A practical and clean layout for quick rate checks and direct contact with the exchange office.",
"chip_hours":"Working Hours",
"chip_hours_value":"Visible",
"chip_notes":"Notes",
"chip_notes_value":"Editable",
"rates_eyebrow":"Exchange Rates",
"rates_title":"Exchange Rates",
"rates_text":"The exchange table remains the most important part of the homepage and stays easy to read on both desktop and mobile.",
"rates_card_title":"Buy / Sell Rates",
"hours_label":"Working Hours:",
"rates_card_text":"A clear overview of daily rates for visitors",
"table_currency":"Currency",
"table_buy":"Buy",
"table_sell":"Sell",
"notes_eyebrow":"Notes",
"notes_title":"Announcements",
"notes_text":"Short and practical messages below the exchange list for important daily information.",
"contact_eyebrow":"Contact",
"contact_title":"Call Us Directly",
"contact_text":"Quick contact for rate checks, information, and service.",
"faq_eyebrow":"Questions",
"faq_title":"Exchange Rate FAQ",
"faq_items":[
{"question":"Where is the exchange office in Skopje?","answer":"EURO MARFI is located at ul. Hristo Tatarchev 33a, Skopje 1000. The Location page includes the map, address, and direct phone contact."},
{"question":"When is the exchange rate list updated?","answer":"The exchange rate list is checked and updated every day by the owner with the latest buy and sell rates."},
{"question":"Which currencies are shown on the exchange rate list?","answer":"The page shows buy and sell rates for EUR, USD, GBP, CHF, CAD, AUD, RSD, BGN, TRY, and ALB. For other currencies, please call us directly."},
],
"call_label":"Call now",
"moneygram_title":"MoneyGram Transfer Services",
"moneygram_text":"The exchange office also supports MoneyGram money transfer services.",
"location_eyebrow":"Location",
"location_title":"Visit Us",
"location_link":"Open location page",
"counter_eyebrow":"Visitors",
"counter_text":"Website visitor counter.",
"location_page_title":"Location",
"address_label":"Address",
"location_page_eyebrow":"Contact & Directions",
"location_page_text":"A clear page with address details, direct phone contact, and a map for finding the exchange office more easily.",
"location_exact_address":"Exact Address",
"location_visit_title":"Visit the Exchange Office",
"location_visit_text":"This is the main business address shown on the page and in the contact section.",
"map_title":"Location map",
"gallery_page_title":"Gallery",
"gallery_page_eyebrow":"Our Exchange Office",
"gallery_page_text":"A gallery prepared for exchange office photos, interior shots, and service visuals while keeping the same modern visual identity.",
"gallery_source":"Image Source",
"gallery_source_text":"Local files in static/images",
"gallery_item":"Image",
"footer_text":"Trusted exchange office since 2007",
"footer_rights":"All rights reserved",
"lang_label":"Language",
"currency_default_name":"Currency",
"viber_label":"Chat on Viber",
"whatsapp_label":"Chat on WhatsApp",
"contact_dock_label":"Contact options",
"gallery_prev_label":"Previous photo",
"gallery_next_label":"Next photo",
"gallery_navigation_label":"Gallery navigation",
"gallery_show_photo_label":"Show photo",
"login_page_title":"Admin Login",
"login_title":"Admin Login",
"login_owner_only":"Owner access only",
"username_label":"Username",
"password_label":"Password",
"login_submit":"Log in",
"admin_page_title":"Admin Panel",
"admin_kicker":"Control Panel",
"admin_title":"Content Editing",
"admin_subtitle_text":"Fill in the fields and save. Public pages support Macedonian and English versions while exchange rates remain shared.",
"admin_preview":"View site",
"admin_logout":"Log out",
"admin_basic_title":"Basic Information",
"admin_basic_text":"Content for the homepage and location page",
"admin_daily_info_mk":"Daily Info MK",
"admin_daily_info_en":"Daily Info EN",
"admin_working_hours_mk":"Working Hours MK",
"admin_working_hours_en":"Working Hours EN",
"admin_phone_1":"Phone 1",
"admin_phone_2":"Phone 2",
"admin_address":"Address",
"admin_map_link":"Map Link",
"admin_notes_title":"Notes Below Exchange Rates",
"admin_notes_text":"Separate text fields for MK and EN",
"admin_note_1_mk":"Note 1 MK",
"admin_note_1_en":"Note 1 EN",
"admin_note_2_mk":"Note 2 MK",
"admin_note_2_en":"Note 2 EN",
"admin_note_3_mk":"Note 3 MK",
"admin_note_3_en":"Note 3 EN",
"admin_rates_title":"Exchange Rates",
"admin_rates_text":"All existing currencies remain editable",
"admin_flag_label":"Flag Label",
"admin_buy_label":"Buy Rate",
"admin_sell_label":"Sell Rate",
"admin_save_changes":"Save Changes",
},
}

DEFAULT_DATA ={
"business":{
"name":{"mk":"Р•РЈР Рћ РњРђР Р¤Р","en":"EURO MARFI"},
"tagline":{
"mk":"Курсна листа и брза услуга за менување девизи",
"en":"Exchange rates and fast foreign currency service",
},
"daily_info":{
"mk":"Курсна листа за 16.04.2026",
"en":"Exchange rates for 16.04.2026",
},
"working_hours":{
"mk":"Понеделник - Петок: 09 до 16 часот",
"en":"Monday - Friday: 09:00 to 16:00",
},
"phones":["075 573 000","02 529 7870"],
"address":"ul. Hristo Tatarchev 33a, Skopje 1000",
"map_embed_url":"https://www.google.com/maps?q=ul.+Hristo+Tatarchev+33a,+Skopje+1000&output=embed",
# Replace these placeholder chat links later with the owner's real Viber and WhatsApp contacts.
"viber_link":"viber://chat?number=%2B38975573000",
"whatsapp_link":"https://wa.me/38975573000",
},
"notes":{
"mk":[
"За да ви откупиме евра (над 5000) цената е 61.55",
"За да ви продадеме евра (над 5000) цената е 61.69",
"За да ви продадеме долари (над 5000) цената е 52.30",
],
"en":[
"For buying euros from you (over 5000), the rate is 61.55",
"For selling euros to you (over 5000), the rate is 61.69",
"For selling dollars to you (over 5000), the rate is 52.30",
],
},
"currencies":[
{"code":"EUR","name":{"mk":"Евро","en":"Euro"},"buy":"61.45","sell":"61.75","flag":"ЕУ","flag_image":"images/flags/eur.svg"},
{"code":"USD","name":{"mk":"Американски долар","en":"US Dollar"},"buy":"51.60","sell":"52.90","flag":"САД","flag_image":"images/flags/usd.svg"},
{"code":"GBP","name":{"mk":"Британска фунта","en":"British Pound"},"buy":"70.00","sell":"71.50","flag":"ОК","flag_image":"images/flags/gbp.svg"},
{"code":"CHF","name":{"mk":"РЁРІР°СС†Р°СЂСЃРєРё С„СЂР°РЅРє","en":"Swiss Franc"},"buy":"66.20","sell":"67.70","flag":"CH","flag_image":"images/flags/chf.svg"},
{"code":"CAD","name":{"mk":"Канадски долар","en":"Canadian Dollar"},"buy":"37.20","sell":"38.70","flag":"CA","flag_image":"images/flags/cad.svg"},
{"code":"AUD","name":{"mk":"Австралиски долар","en":"Australian Dollar"},"buy":"36.50","sell":"38.00","flag":"AU","flag_image":"images/flags/aud.svg"},
{"code":"RSD","name":{"mk":"Српски динар","en":"Serbian Dinar"},"buy":"0.50","sell":"0.54","flag":"RS","flag_image":"images/flags/rsd.svg"},
{"code":"BGN","name":{"mk":"Бугарски лев","en":"Bulgarian Lev"},"buy":"28.00","sell":"0.00","flag":"BG","flag_image":"images/flags/bgn.svg"},
{"code":"TRY","name":{"mk":"Турска лира","en":"Turkish Lira"},"buy":"1.00","sell":"1.90","flag":"TR","flag_image":"images/flags/try.svg"},
{"code":"ALB","name":{"mk":"Албански лек","en":"Albanian Lek"},"buy":"0.55","sell":"0.65","flag":"AL","flag_image":"images/flags/alb.svg"},
],
"gallery":[
{
"image":"images/gallery/menuva5.jpg",
"title":{"mk":"Менувачница ЕУРО МАРФИ","en":"EURO MARFI Exchange Office"},
"description":{
"mk":"Надворешен поглед од менувачницата ЕУРО МАРФИ.",
"en":"Outdoor view of EURO MARFI exchange office.",
},
},
{
"image":"images/gallery/menuva1.jpg",
"title":{"mk":"Влез во менувачницата","en":"Exchange Office Entrance"},
"description":{
"mk":"Поглед кон влезот и услугата за менување девизи.",
"en":"View of the entrance and foreign currency exchange service.",
},
},
{
"image":"images/gallery/menuva4.jpg",
"title":{"mk":"Локација","en":"Location"},
"description":{
"mk":"Фотографија од објектот и околината.",
"en":"Photo of the office and surroundings.",
},
},
{
"image":"images/gallery/menuva.jpg",
"title":{"mk":"Работно време","en":"Working Hours"},
"description":{
"mk":"Информација за работното време на менувачницата.",
"en":"Working hours information for the exchange office.",
},
},
{
"image":"images/gallery/menuva3.jpg",
"title":{"mk":"Излог","en":"Storefront"},
"description":{
"mk":"Дополнителен поглед од излогот и објектот.",
"en":"Additional view of the storefront and office.",
},
},
],
"visitor_count":LEGACY_VISITOR_COUNT ,
}


def supabase_is_configured ()->bool :
    return bool (SUPABASE_URL and SUPABASE_KEY )


def supabase_headers (extra_headers :dict |None =None )->dict :
    headers ={
    "apikey":SUPABASE_KEY ,
    "Authorization":f"Bearer {SUPABASE_KEY }",
    }
    if extra_headers :
        headers .update (extra_headers )
    return headers


def supabase_request (method :str ,path :str ,payload =None ,headers :dict |None =None ,raw_body :bytes |None =None ):
    if not supabase_is_configured ():
        return None
    url =f"{SUPABASE_URL }{path }"
    body =raw_body
    request_headers =supabase_headers (headers )
    if payload is not None :
        body =json .dumps (payload ).encode ("utf-8")
        request_headers .setdefault ("Content-Type","application/json")
    request_obj =Request (url ,data =body ,headers =request_headers ,method =method )
    try :
        with urlopen (request_obj ,timeout =SUPABASE_TIMEOUT )as response :
            response_body =response .read ()
            if not response_body :
                return None
            return json .loads (response_body .decode ("utf-8"))
    except HTTPError as error :
        detail =error .read ().decode ("utf-8","replace")
        raise RuntimeError (f"Supabase request failed: {method } {path } -> {error .code } {detail }")from error
    except URLError as error :
        raise RuntimeError (f"Supabase request failed: {method } {path } -> {error }")from error


def load_supabase_json (key :str ):
    encoded_key =quote (key ,safe ="")
    encoded_table =quote (SUPABASE_TABLE ,safe ="")
    rows =supabase_request (
    "GET",
    f"/rest/v1/{encoded_table }?key=eq.{encoded_key }&select=value&limit=1",
    headers ={"Accept":"application/json"},
    )
    if not rows :
        return None
    return rows [0 ].get ("value")


def save_supabase_json (key :str ,value :dict )->None :
    encoded_table =quote (SUPABASE_TABLE ,safe ="")
    supabase_request (
    "POST",
    f"/rest/v1/{encoded_table }",
    payload ={"key":key ,"value":value },
    headers ={"Prefer":"resolution=merge-duplicates,return=minimal"},
    )


def load_local_json (path :Path ,default_value :dict )->dict :
    path .parent .mkdir (parents =True ,exist_ok =True )
    if not path .exists ():
        with path .open ("w",encoding ="utf-8")as file :
            json .dump (default_value ,file ,indent =2 ,ensure_ascii =False )
    with path .open ("r",encoding ="utf-8")as file :
        return json .load (file )


def save_local_json (path :Path ,value :dict )->None :
    path .parent .mkdir (parents =True ,exist_ok =True )
    with path .open ("w",encoding ="utf-8")as file :
        json .dump (value ,file ,indent =2 ,ensure_ascii =False )


def upload_supabase_media (file_storage ,kind :str ,allowed_extensions :set [str ])->str :
    original =secure_filename (file_storage .filename or "")
    ext =original .rsplit (".",1 )[-1 ].lower ()if "."in original else ""
    if ext not in allowed_extensions :
        return ""
    content =file_storage .read ()
    if not content :
        return ""
    prefix =f"{SUPABASE_MEDIA_PREFIX }/"if SUPABASE_MEDIA_PREFIX else ""
    object_path =f"{prefix }{kind }/{uuid .uuid4 ().hex }.{ext }"
    encoded_bucket =quote (SUPABASE_STORAGE_BUCKET ,safe ="")
    encoded_path =quote (object_path ,safe ="/")
    content_type =file_storage .mimetype or "application/octet-stream"
    supabase_request (
    "POST",
    f"/storage/v1/object/{encoded_bucket }/{encoded_path }",
    headers ={"Content-Type":content_type ,"x-upsert":"true"},
    raw_body =content,
    )
    return f"{SUPABASE_URL }/storage/v1/object/public/{encoded_bucket }/{encoded_path }"


def public_media_url (path :str )->str :
    if not path :
        return ""
    if path .startswith (("http://","https://","//")):
        return path
    return url_for ("static",filename =path )


class TextHTMLParser (HTMLParser ):
    def __init__ (self ):
        super ().__init__ ()
        self .parts =[]

    def handle_data (self ,data ):
        cleaned =unescape (data ).strip ()
        if cleaned :
            self .parts .append (cleaned )

    def text (self )->str :
        return "\n".join (self .parts )


def skopje_now ()->datetime :
    return datetime .now (SKOPJE_TZ )if SKOPJE_TZ else datetime .now ()


def format_rate_date (lang :str ,date_value :datetime |None =None )->str :
    current_date =date_value or skopje_now ()
    formatted =current_date .strftime ("%d.%m.%Y")
    if lang =="en":
        return f"Exchange rates for {formatted}"
    return f"Курсна листа за {formatted}"


def normalize_rate_value (value :str )->str :
    return value .replace (",",".").strip ()


def translate_live_note (note :str )->str :
    normalized =re .sub (r"\s+"," ",note ).strip ()
    normalized =normalized .replace ("!!!!!","").replace ("!!!!","").replace ("!!!","").strip ()
    match =re .search (r"За да ви откупиме евра.*?цената е\s*([0-9]+(?:[.,][0-9]+)?)",normalized ,re .IGNORECASE )
    if match :
        return f"For buying euros from you over 5000, the rate is {normalize_rate_value (match .group (1 ))}"
    match =re .search (r"За да ви продадеме евра.*?цената е\s*([0-9]+(?:[.,][0-9]+)?)",normalized ,re .IGNORECASE )
    if match :
        return f"For selling euros to you over 5000, the rate is {normalize_rate_value (match .group (1 ))}"
    match =re .search (r"За да ви продадеме долари.*?цената е\s*([0-9]+(?:[.,][0-9]+)?)",normalized ,re .IGNORECASE )
    if match :
        return f"For selling dollars to you over 5000, the rate is {normalize_rate_value (match .group (1 ))}"
    return normalized


def translate_working_hours (hours_text :str )->str :
    normalized =re .sub (r"\s+"," ",hours_text ).strip ()
    match =re .search (
    r"Понеделник\s*-\s*Петок\s*:\s*(\d{1,2})(?::(\d{2}))?\s*до\s*(\d{1,2})(?::(\d{2}))?",
    normalized ,
    re .IGNORECASE ,
    )
    if match :
        start_hour =int (match .group (1 ))
        start_minute =match .group (2 )or "00"
        end_hour =int (match .group (3 ))
        end_minute =match .group (4 )or "00"
        return f"Monday - Friday: {start_hour:02d}:{start_minute} to {end_hour:02d}:{end_minute}"
    match =re .search (
    r"Понеделник\s*-\s*Недела\s*:\s*(\d{1,2})(?::(\d{2}))?\s*до\s*(\d{1,2})(?::(\d{2}))?",
    normalized ,
    re .IGNORECASE ,
    )
    if match :
        start_hour =int (match .group (1 ))
        start_minute =match .group (2 )or "00"
        end_hour =int (match .group (3 ))
        end_minute =match .group (4 )or "00"
        return f"Monday - Sunday: {start_hour:02d}:{start_minute} to {end_hour:02d}:{end_minute}"
    return normalized


def extract_working_hours (text :str )->str :
    patterns =[
    r"Понеделник\s*-\s*Петок\s*:\s*\d{1,2}(?::\d{2})?\s*до\s*\d{1,2}(?::\d{2})?\s*часот",
    r"Понеделник\s*-\s*Недела\s*:\s*\d{1,2}(?::\d{2})?\s*до\s*\d{1,2}(?::\d{2})?\s*часот",
    r"Понеделник\s*-\s*Сабота\s*:\s*\d{1,2}(?::\d{2})?\s*до\s*\d{1,2}(?::\d{2})?\s*часот",
    ]
    for pattern in patterns :
        match =re .search (pattern ,text ,re .IGNORECASE )
        if match :
            return re .sub (r"\s+"," ",match .group (0 )).strip ()
    return ""


def extract_phone_numbers (text :str )->list [str ]:
    phones =[]
    for match in re .finditer (r"(?:☎\s*)?(0\d{2}\s*\d{3}\s*\d{3}|0\d{8})",text ):
        phone =re .sub (r"\s+"," ",match .group (1 )).strip ()
        if len (phone )==9 and " "not in phone :
            phone =f"{phone [:3]} {phone [3:6]} {phone [6:]}"
        if phone not in phones :
            phones .append (phone )
    return phones


def parse_live_rates_html (html :str )->dict :
    parser =TextHTMLParser ()
    parser .feed (html )
    text =parser .text ()
    compact_text =re .sub (r"[ \t]+"," ",text )
    currency_codes =[currency ["code"]for currency in DEFAULT_DATA ["currencies"]]
    parsed_rates ={}

    for code in currency_codes :
        match =re .search (
        rf"\b{re.escape (code )}\b\s+([0-9]+(?:[.,][0-9]+)?)\s+([0-9]+(?:[.,][0-9]+)?)",
        compact_text ,
        re .IGNORECASE ,
        )
        if match :
            parsed_rates [code ]={
            "buy":normalize_rate_value (match .group (1 )),
            "sell":normalize_rate_value (match .group (2 )),
            }

    if len (parsed_rates )<5 :
        raise ValueError ("The source page did not contain enough valid exchange-rate rows.")

    note_matches =re .findall (r"За да ви [^\n\r]+",text )
    notes_mk =[re .sub (r"\s+"," ",note ).strip ()for note in note_matches if note .strip ()]
    notes_mk =notes_mk [:3 ]or deepcopy (DEFAULT_DATA ["notes"]["mk"])

    date_match =re .search (r"\b(\d{2}\.\d{2}\.\d{4})\b",text )
    source_date =date_match .group (1 )if date_match else ""
    working_hours_mk =extract_working_hours (text )
    phones =extract_phone_numbers (text )

    return {
    "source_url":LIVE_RATES_SOURCE_URL ,
    "source_date":source_date ,
    "synced_at":skopje_now ().isoformat (),
    "rates":parsed_rates ,
    "notes_mk":notes_mk ,
    "notes_en":[translate_live_note (note )for note in notes_mk ],
    "working_hours_mk":working_hours_mk ,
    "working_hours_en":translate_working_hours (working_hours_mk )if working_hours_mk else "",
    "phones":phones ,
    }


def fetch_live_rates ()->dict :
    request_obj =Request (
    LIVE_RATES_SOURCE_URL ,
    headers ={"User-Agent":"EURO-MARFI live rates sync/1.0"},
    )
    with urlopen (request_obj ,timeout =LIVE_RATES_TIMEOUT )as response :
        raw_html =response .read ()
    html =raw_html .decode ("utf-8","replace")
    return parse_live_rates_html (html )


def load_live_rates_cache ()->dict |None :
    if supabase_is_configured ():
        cached =load_supabase_json ("live_rates_cache")
        return cached if isinstance (cached ,dict )else None
    if not LIVE_RATES_CACHE_FILE .exists ():
        return None
    try :
        return load_local_json (LIVE_RATES_CACHE_FILE ,{})
    except (json .JSONDecodeError ,OSError ):
        return None


def save_live_rates_cache (cache :dict )->None :
    if supabase_is_configured ():
        save_supabase_json ("live_rates_cache",cache )
        return
    save_local_json (LIVE_RATES_CACHE_FILE ,cache )


def cache_is_fresh (cache :dict )->bool :
    try :
        synced_at =datetime .fromisoformat (cache .get ("synced_at",""))
    except (TypeError ,ValueError ):
        return False
    return (skopje_now ()-synced_at ).total_seconds ()<LIVE_RATES_CACHE_SECONDS


def get_live_rates_payload ()->dict |None :
    cache =load_live_rates_cache ()
    if cache and cache_is_fresh (cache ):
        return cache
    try :
        live_rates =fetch_live_rates ()
        save_live_rates_cache (live_rates )
        return live_rates
    except (HTTPError ,URLError ,TimeoutError ,ValueError ,OSError ):
        return cache


def apply_live_rates (data :dict )->dict :
    live_rates =get_live_rates_payload ()
    today =skopje_now ()
    data ["business"]["daily_info"]={
    "mk":format_rate_date ("mk",today ),
    "en":format_rate_date ("en",today ),
    }
    if not live_rates :
        return data

    working_hours_mk =live_rates .get ("working_hours_mk","")
    working_hours_en =live_rates .get ("working_hours_en","")
    if working_hours_mk :
        data ["business"]["working_hours"]={
        "mk":working_hours_mk ,
        "en":working_hours_en or translate_working_hours (working_hours_mk ),
        }

    phones =live_rates .get ("phones")or []
    if phones :
        data ["business"]["phones"]=phones

    live_rate_rows =live_rates .get ("rates",{})
    for currency in data .get ("currencies",[]):
        rate_row =live_rate_rows .get (currency .get ("code",""))
        if rate_row :
            currency ["buy"]=rate_row .get ("buy",currency .get ("buy",""))
            currency ["sell"]=rate_row .get ("sell",currency .get ("sell",""))

    notes_mk =live_rates .get ("notes_mk")or []
    notes_en =live_rates .get ("notes_en")or []
    if notes_mk :
        data ["notes"]["mk"]=notes_mk
        data ["notes"]["en"]=notes_en if len (notes_en )==len (notes_mk )else [translate_live_note (note )for note in notes_mk ]
    return data


def ensure_data_file ()->None :
    if supabase_is_configured ():
        if load_supabase_json ("site_data")is None :
            seed_data =load_local_json (DATA_FILE ,deepcopy (DEFAULT_DATA ))if DATA_FILE .exists ()else deepcopy (DEFAULT_DATA )
            save_supabase_json ("site_data",seed_data )
        return
    DATA_FILE .parent .mkdir (parents =True ,exist_ok =True )
    if not DATA_FILE .exists ():
        save_local_json (DATA_FILE ,deepcopy (DEFAULT_DATA ))


def default_admin_settings ()->dict :
    return {
    "username":ADMIN_USERNAME ,
    "password_hash":generate_password_hash (ADMIN_PASSWORD ),
    "totp_enabled":False ,
    "totp_secret":"",
    }


def save_admin_settings (settings :dict )->None :
    if supabase_is_configured ():
        save_supabase_json ("admin_settings",settings )
        return
    save_local_json (ADMIN_SETTINGS_FILE ,settings )


def ensure_admin_settings ()->None :
    if supabase_is_configured ():
        if load_supabase_json ("admin_settings")is None :
            seed_settings =load_local_json (ADMIN_SETTINGS_FILE ,default_admin_settings ())if ADMIN_SETTINGS_FILE .exists ()else default_admin_settings ()
            save_supabase_json ("admin_settings",seed_settings )
        return
    ADMIN_SETTINGS_FILE .parent .mkdir (parents =True ,exist_ok =True )
    if not ADMIN_SETTINGS_FILE .exists ():
        save_local_json (ADMIN_SETTINGS_FILE ,default_admin_settings ())


def load_admin_settings ()->dict :
    ensure_admin_settings ()
    if supabase_is_configured ():
        current_settings =load_supabase_json ("admin_settings")or default_admin_settings ()
    else :
        current_settings =load_local_json (ADMIN_SETTINGS_FILE ,default_admin_settings ())

    defaults =default_admin_settings ()
    settings ={
    "username":(current_settings .get ("username")or defaults ["username"]).strip ()or defaults ["username"],
    "password_hash":current_settings .get ("password_hash")or defaults ["password_hash"],
    "totp_enabled":bool (current_settings .get ("totp_enabled",False )),
    "totp_secret":(current_settings .get ("totp_secret")or "").strip (),
    }

    if settings ["totp_enabled"]and not settings ["totp_secret"]:
        settings ["totp_enabled"]=False

    return settings


def get_pending_totp_secret ()->str :
    pending_secret =session .get ("pending_totp_secret","").strip ()
    if not pending_secret :
        pending_secret =pyotp .random_base32 ()
        session ["pending_totp_secret"]=pending_secret
    return pending_secret


def clear_pending_totp_secret ()->None :
    session .pop ("pending_totp_secret",None )


def build_totp_setup_payload (username :str ,secret :str )->tuple [str ,str ]:
    totp =pyotp .TOTP (secret )
    provisioning_uri =totp .provisioning_uri (name =username ,issuer_name ="EURO MARFI")
    qr_image =qrcode .make (provisioning_uri ,image_factory =SvgPathImage ,box_size =5 ,border =2 )
    qr_buffer =io .BytesIO ()
    qr_image .save (qr_buffer )
    return qr_buffer .getvalue ().decode ("utf-8"),provisioning_uri


def localized_value (value ,lang :str ):
    if isinstance (value ,dict ):
        return value .get (lang )or value .get ("mk")or next (iter (value .values ()),"")
    return value


def normalize_localized_field (value ,default_value ):
    if isinstance (default_value ,dict ):
        normalized =deepcopy (default_value )
        if isinstance (value ,dict ):
            for lang in SUPPORTED_LANGUAGES :
                if value .get (lang ):
                    normalized [lang ]=value [lang ]
        elif isinstance (value ,str )and value .strip ():
            normalized ["mk"]=value
        return normalized
    return value if value not in (None ,"")else deepcopy (default_value )


def load_data ()->dict :
    ensure_data_file ()
    if supabase_is_configured ():
        data =load_supabase_json ("site_data")or deepcopy (DEFAULT_DATA )
    else :
        data =load_local_json (DATA_FILE ,deepcopy (DEFAULT_DATA ))

    data .setdefault ("business",{})
    for key ,default_value in DEFAULT_DATA ["business"].items ():
        current_value =data ["business"].get (key )
        data ["business"][key ]=normalize_localized_field (current_value ,default_value )

    current_notes =data .get ("notes")
    if isinstance (current_notes ,list ):
        data ["notes"]={"mk":current_notes ,"en":deepcopy (DEFAULT_DATA ["notes"]["en"])}
    elif not isinstance (current_notes ,dict ):
        data ["notes"]=deepcopy (DEFAULT_DATA ["notes"])
    else :
        for lang in SUPPORTED_LANGUAGES :
            if not isinstance (current_notes .get (lang ),list ):
                current_notes [lang ]=deepcopy (DEFAULT_DATA ["notes"][lang ])
        data ["notes"]=current_notes

    current_gallery =data .get ("gallery")
    if not isinstance (current_gallery ,list )or not current_gallery :
        data ["gallery"]=deepcopy (DEFAULT_DATA ["gallery"])
    else :
        normalized_gallery =[]
        for item in current_gallery :
            if not isinstance (item ,dict ):
                continue
            normalized_item ={
                "type":item .get ("type","image"),
                "image":item .get ("image",""),
                "video_url":item .get ("video_url",""),
                "title":normalize_localized_field (item .get ("title"),{"mk":"","en":""}),
                "description":normalize_localized_field (item .get ("description"),{"mk":"","en":""}),
            }
            normalized_gallery .append (normalized_item )
        data ["gallery"]=normalized_gallery if normalized_gallery else deepcopy (DEFAULT_DATA ["gallery"])

    default_currencies ={currency ["code"]:currency for currency in DEFAULT_DATA ["currencies"]}
    normalized_currencies =[]
    for default_currency in DEFAULT_DATA ["currencies"]:
        existing_currency =next (
        (currency for currency in data .get ("currencies",[])if currency .get ("code")==default_currency ["code"]),
        {},
        )
        currency =dict (default_currency )
        currency ["buy"]=existing_currency .get ("buy",default_currency ["buy"])
        currency ["sell"]=existing_currency .get ("sell",default_currency ["sell"])
        currency ["flag"]=existing_currency .get ("flag",default_currency ["flag"])
        currency ["flag_image"]=existing_currency .get ("flag_image",default_currency ["flag_image"])
        currency ["name"]=normalize_localized_field (existing_currency .get ("name"),default_currency ["name"])
        normalized_currencies .append (currency )
    data ["currencies"]=normalized_currencies

    data ["visitor_count"]=max (int (data .get ("visitor_count",0 )),LEGACY_VISITOR_COUNT )
    return apply_live_rates (data )


def save_data (data :dict )->None :
    if supabase_is_configured ():
        save_supabase_json ("site_data",data )
        return
    save_local_json (DATA_FILE ,data )


def save_gallery_image (file_storage )->str :
    if supabase_is_configured ()and SUPABASE_STORAGE_BUCKET :
        return upload_supabase_media (file_storage ,"gallery",_GALLERY_ALLOWED_EXTENSIONS )
    original =secure_filename (file_storage .filename or "")
    ext =original .rsplit (".",1 )[-1 ].lower ()if "."in original else ""
    if ext not in _GALLERY_ALLOWED_EXTENSIONS :
        return ""
    GALLERY_DIR .mkdir (parents =True ,exist_ok =True )
    unique_name =f"{uuid .uuid4 ().hex }.{ext }"
    file_storage .save (GALLERY_DIR /unique_name )
    return f"images/gallery/{unique_name }"


def save_gallery_video (file_storage )->str :
    if supabase_is_configured ()and SUPABASE_STORAGE_BUCKET :
        return upload_supabase_media (file_storage ,"videos",_VIDEO_ALLOWED_EXTENSIONS )
    original =secure_filename (file_storage .filename or "")
    ext =original .rsplit (".",1 )[-1 ].lower ()if "."in original else ""
    if ext not in _VIDEO_ALLOWED_EXTENSIONS :
        return ""
    VIDEO_DIR .mkdir (parents =True ,exist_ok =True )
    unique_name =f"{uuid .uuid4 ().hex }.{ext }"
    file_storage .save (VIDEO_DIR /unique_name )
    return f"videos/{unique_name }"


def is_logged_in ()->bool :
    return session .get ("admin_logged_in",False )


def get_current_language ()->str :
    endpoint =request .endpoint or ""
    if endpoint .startswith ("en_"):
        return "en"
    public_endpoints ={item [0 ]for item in PUBLIC_SITEMAP_PAGES }
    if CANONICAL_ENDPOINTS .get (endpoint ,endpoint )in public_endpoints :
        return "mk"
    lang =session .get ("lang","mk")
    return lang if lang in SUPPORTED_LANGUAGES else "mk"


def parse_time_value (raw_value :str )->time |None :
    match =re .search (r"(\d{1,2})(?::(\d{2}))?",raw_value )
    if not match :
        return None
    hour =int (match .group (1 ))
    minute =int (match .group (2 )or 0 )
    if hour >23 or minute >59 :
        return None
    return time (hour ,minute )


def parse_working_hours_range (raw_value :str )->tuple [time ,time ]|None :
    matches =re .findall (r"(\d{1,2})(?::(\d{2}))?",raw_value )
    if len (matches )<2 :
        return None

    start_hours ,start_minutes =matches [0 ]
    end_hours ,end_minutes =matches [1 ]
    start =parse_time_value (f"{start_hours }:{start_minutes or '00'}")
    end =parse_time_value (f"{end_hours }:{end_minutes or '00'}")
    if not start or not end :
        return None
    return start ,end


def parse_allowed_weekdays (raw_value :str )->set [int ]:
    lower_value =raw_value .lower ()
    day_names ={
    0 :("monday","понеделник"),
    1 :("tuesday","вторник"),
    2 :("wednesday","среда"),
    3 :("thursday","четврток"),
    4 :("friday","петок"),
    5 :("saturday","сабота"),
    6 :("sunday","недела"),
    }

    found_days =[]
    for day_index ,aliases in day_names .items ():
        positions =[lower_value .find (alias )for alias in aliases if alias in lower_value ]
        if positions :
            found_days .append ((min (positions ),day_index ))

    if not found_days :
        return set (range (7 ))

    found_days .sort ()
    ordered_days =[day_index for _ ,day_index in found_days ]
    if len (ordered_days )==1 :
        return {ordered_days [0 ]}

    start_day =ordered_days [0 ]
    end_day =ordered_days [1 ]
    if start_day <=end_day :
        return set (range (start_day ,end_day +1 ))
    return set (range (start_day ,7 ))|set (range (0 ,end_day +1 ))


def get_business_status (working_hours )->dict :
    raw_hours =working_hours .get ("en")or working_hours .get ("mk")or ""
    parsed_hours =parse_working_hours_range (raw_hours )

    if parsed_hours :
        start_time ,end_time =parsed_hours
        display_hours =f"{start_time .strftime ('%H:%M')} - {end_time .strftime ('%H:%M')}"
        allowed_weekdays =parse_allowed_weekdays (raw_hours )
        now =datetime .now (SKOPJE_TZ )if SKOPJE_TZ else datetime .now ()
        current_time =now .time ()

        if start_time <=end_time :
            is_open =now .weekday ()in allowed_weekdays and start_time <=current_time <end_time
        else :
            is_open =current_time >=start_time or current_time <end_time
    else :
        display_hours =localized_value (working_hours ,"mk")
        is_open =False

    return {
    "is_open":is_open ,
    "display_hours":display_hours ,
    }


def increment_visitor_count ()->int :
    data =load_data ()
    if supabase_is_configured ():
        return int (data .get ("visitor_count",LEGACY_VISITOR_COUNT ))
    if not session .get ("visit_counted"):
        data ["visitor_count"]=max (int (data .get ("visitor_count",0 )),LEGACY_VISITOR_COUNT )+1
        save_data (data )
        session ["visit_counted"]=True
    return int (data .get ("visitor_count",LEGACY_VISITOR_COUNT ))

def update_site_data_from_admin_form (data :dict ,form ,files =None )->dict :
    rate_date =form .get ("rate_date","").strip ()
    if rate_date :
        try :
            parsed_rate_date =datetime .strptime (rate_date ,"%Y-%m-%d")
            display_rate_date =parsed_rate_date .strftime ("%d.%m.%Y")
            data ["business"]["daily_info"]={
            "mk":f"Курсна листа за {display_rate_date}",
            "en":f"Exchange rates for {display_rate_date}",
            }
        except ValueError :
            pass
    elif "daily_info_mk"in form or "daily_info_en"in form :
        data ["business"]["daily_info"]={
        "mk":form .get ("daily_info_mk",localized_value (data ["business"].get ("daily_info"),"mk")).strip (),
        "en":form .get ("daily_info_en",localized_value (data ["business"].get ("daily_info"),"en")).strip (),
        }
    data ["business"]["working_hours"]={
    "mk":form .get ("working_hours_mk","").strip (),
    "en":form .get ("working_hours_en","").strip (),
    }
    data ["business"]["phones"]=[
    form .get ("phone_1","").strip (),
    form .get ("phone_2","").strip (),
    ]
    data ["business"]["address"]=form .get ("address","").strip ()
    data ["business"]["map_embed_url"]=form .get ("map_embed_url","").strip ()

    data ["notes"]={
    "mk":[
    form .get ("note_1_mk","").strip (),
    form .get ("note_2_mk","").strip (),
    form .get ("note_3_mk","").strip (),
    ],
    "en":[
    form .get ("note_1_en","").strip (),
    form .get ("note_2_en","").strip (),
    form .get ("note_3_en","").strip (),
    ],
    }

    updated_gallery =[]
    for index ,item in enumerate (data .get ("gallery",[]),start =1 ):
        if form .get (f"gallery_delete_{index }")=="1":
            continue
        updated_item =dict (item )
        updated_item ["type"]=form .get (f"gallery_type_{index }",item .get ("type","image"))
        updated_item ["video_url"]=form .get (f"gallery_video_url_{index }",item .get ("video_url","")).strip ()
        updated_item ["title"]={
        "mk":form .get (f"gallery_title_{index }_mk",localized_value (item .get ("title"),"mk")).strip (),
        "en":form .get (f"gallery_title_{index }_en",localized_value (item .get ("title"),"en")).strip (),
        }
        updated_item ["description"]={
        "mk":form .get (f"gallery_description_{index }_mk",localized_value (item .get ("description"),"mk")).strip (),
        "en":form .get (f"gallery_description_{index }_en",localized_value (item .get ("description"),"en")).strip (),
        }
        if files :
            uploaded_img =files .get (f"gallery_image_{index }")
            if uploaded_img and uploaded_img .filename :
                saved =save_gallery_image (uploaded_img )
                if saved :
                    updated_item ["image"]=saved
            uploaded_vid =files .get (f"gallery_video_{index }")
            if uploaded_vid and uploaded_vid .filename :
                saved =save_gallery_video (uploaded_vid )
                if saved :
                    updated_item ["video_url"]=saved
        updated_gallery .append (updated_item )

    new_count =int (form .get ("gallery_new_count",0 )or 0 )
    for n in range (1 ,new_count +1 ):
        if form .get (f"gallery_new_{n }_skip")=="1":
            continue
        new_item ={
        "type":form .get (f"gallery_new_{n }_type","image"),
        "image":"",
        "video_url":form .get (f"gallery_new_{n }_video_url","").strip (),
        "title":{
        "mk":form .get (f"gallery_new_{n }_title_mk","").strip (),
        "en":form .get (f"gallery_new_{n }_title_en","").strip (),
        },
        "description":{
        "mk":form .get (f"gallery_new_{n }_description_mk","").strip (),
        "en":form .get (f"gallery_new_{n }_description_en","").strip (),
        },
        }
        if files :
            uploaded_img =files .get (f"gallery_new_{n }_image")
            if uploaded_img and uploaded_img .filename :
                saved =save_gallery_image (uploaded_img )
                if saved :
                    new_item ["image"]=saved
            uploaded_vid =files .get (f"gallery_new_{n }_video")
            if uploaded_vid and uploaded_vid .filename :
                saved =save_gallery_video (uploaded_vid )
                if saved :
                    new_item ["video_url"]=saved
        if new_item ["image"]or new_item ["video_url"]or new_item ["title"]["mk"]or new_item ["title"]["en"]:
            updated_gallery .append (new_item )

    data ["gallery"]=updated_gallery

    updated_currencies =[]
    for currency in data .get ("currencies",[]):
        code =currency ["code"]
        updated_currency =dict (currency )
        updated_currency ["flag"]=form .get (f"flag_{code }",currency .get ("flag","")).strip ()
        updated_currency ["buy"]=form .get (f"buy_{code }",currency .get ("buy","")).strip ()
        updated_currency ["sell"]=form .get (f"sell_{code }",currency .get ("sell","")).strip ()
        updated_currencies .append (updated_currency )

    data ["currencies"]=updated_currencies
    return data


LANDING_PAGE_CONTENT ={
"menuvacnica_skopje":{
"mk":{
"title":"Менувачница Скопје",
"text":"ЕУРО МАРФИ е менувачница во Скопје со дневна курсна листа, куповен и продажен курс, директен телефонски контакт и локација за брза услуга.",
"cta":"Погледнете ја денешната курсна листа",
},
"en":{
"title":"Exchange Office Skopje",
"text":"EURO MARFI is an exchange office in Skopje with daily buy and sell rates, direct phone contact, and a clear location for fast currency exchange service.",
"cta":"View today's exchange rates",
},
},
"menuvacnici_skopje":{
"mk":{
"title":"Менувачници Скопје",
"text":"Ако барате менувачници во Скопје, ЕУРО МАРФИ ја прикажува дневната курсна листа веднаш на почетокот, со работно време, телефон и адреса.",
"cta":"Отворете курсна листа",
},
"en":{
"title":"Exchange Offices Skopje",
"text":"For exchange offices in Skopje, EURO MARFI shows the live exchange table first, with working hours, phone numbers, and location details.",
"cta":"Open exchange rates",
},
},
"exchange_office_skopje":{
"mk":{
"title":"Менувачница Скопје",
"text":"Дневна курсна листа за валути во Скопје со куповен и продажен курс, работно време и директен контакт.",
"cta":"Курсна листа",
},
"en":{
"title":"Exchange Office Skopje",
"text":"Daily currency exchange rates in Skopje with buy and sell rates, working hours, and direct contact information.",
"cta":"Exchange rates",
},
},
}


def get_landing_content (endpoint :str |None =None ,lang :str |None =None )->dict |None :
    canonical_endpoint =normalize_public_endpoint (endpoint or request .endpoint )
    if canonical_endpoint not in LANDING_PAGE_CONTENT :
        return None
    selected_lang =lang or get_current_language ()
    return LANDING_PAGE_CONTENT [canonical_endpoint ].get (selected_lang )or LANDING_PAGE_CONTENT [canonical_endpoint ].get ("mk")


@app .template_filter ("highlight_date")
def highlight_date_filter (value :str )->str :
    return re .sub (r"(\d{2}\.\d{2}\.\d{4})",r'<strong class="date-accent">\1</strong>',value )


@app .template_filter ("date_only")
def date_only_filter (value :str )->str :
    match =re .search (r"\d{2}\.\d{2}\.\d{4}",value or "")
    return match .group (0 )if match else value


@app .context_processor
def inject_site_data ():
    current_lang =get_current_language ()
    site_data =load_data ()
    page_meta =build_page_meta (site_data )
    return {
    "site_data":site_data ,
    "current_lang":current_lang ,
    "ui":UI_TEXT [current_lang ],
    "business_status":get_business_status (site_data ["business"]["working_hours"]),
    "text_for":lambda value :localized_value (value ,current_lang ),
    "public_media_url":public_media_url,
    "page_meta":page_meta ,
    "canonical_url":page_meta ["canonical_url"],
    "alternate_urls":build_alternate_urls (page_meta ["canonical_endpoint"]),
    "localized_url":lambda endpoint ,lang =None :build_localized_page_url (endpoint ,lang or current_lang ),
    "localized_path":lambda endpoint ,lang =None :build_localized_page_path (endpoint ,lang or current_lang ),
    "local_business_schema":build_local_business_schema (site_data ,page_meta ),
    "landing_content":get_landing_content (page_meta ["canonical_endpoint"],current_lang ),
    }


@app .route ("/set-language/<lang>")
def set_language (lang :str ):
    if lang in SUPPORTED_LANGUAGES :
        session ["lang"]=lang
    next_url =request .args .get ("next")or url_for ("index")
    return redirect (next_url )


@app .route ("/index.html")
def legacy_index_html ():
    return redirect (url_for ("index"),code =301 )


@app .route ("/lokacija.html")
def legacy_lokacija_html ():
    return redirect (url_for ("lokacija"),code =301 )


@app .route ("/sliki")
@app .route ("/sliki.html")
def legacy_sliki_html ():
    return redirect (url_for ("galerija"),code =301 )


@app .route ("/%D0%BA%D1%83%D1%80%D1%81%D0%BD%D0%B0-%D0%BB%D0%B8%D1%81%D1%82%D0%B0")
@app .route ("/%D0%BA%D1%83%D1%80%D1%81%D0%BD%D0%B0-%D0%BB%D0%B8%D1%81%D1%82%D0%B0/")
@app .route ("/курсна-листа")
@app .route ("/курсна-листа/")
@app .route ("/kursna-lista")
@app .route ("/kursna-lista/")
def kursna_lista ():
    data =load_data ()
    return render_template ("index.html",data =data )


@app .route ("/en/")
def en_index ():
    session ["lang"]="en"
    data =load_data ()
    return render_template ("index.html",data =data )


@app .route ("/en/exchange-rates")
def en_kursna_lista ():
    session ["lang"]="en"
    data =load_data ()
    return render_template ("index.html",data =data )


@app .route ("/menuvacnica-skopje")
@app .route ("/menuvacnica-skopje/")
def menuvacnica_skopje ():
    data =load_data ()
    return render_template ("index.html",data =data )


@app .route ("/menuvacnici-skopje")
@app .route ("/menuvacnici-skopje/")
def menuvacnici_skopje ():
    data =load_data ()
    return render_template ("index.html",data =data )


@app .route ("/en/exchange-office-skopje")
@app .route ("/en/exchange-office-skopje/")
def en_exchange_office_skopje ():
    session ["lang"]="en"
    data =load_data ()
    return render_template ("index.html",data =data )


@app .route ("/en/exchange-offices-skopje")
@app .route ("/en/exchange-offices-skopje/")
def en_exchange_offices_skopje ():
    session ["lang"]="en"
    data =load_data ()
    return render_template ("index.html",data =data )


@app .route ("/kontakt")
@app .route ("/kontakt/")
@app .route ("/контакт")
@app .route ("/контакт/")
def legacy_contact_page ():
    return redirect (url_for ("lokacija"),code =301 )


@app .route ("/poseta.html")
@app .route ("/proba.html")
@app .route ("/proba2.html")
@app .route ("/proba2")
def legacy_test_pages ():
    return redirect (url_for ("index"),code =301 )


@app .route ("/sliki/<path:filename>")
def legacy_sliki_asset (filename :str ):
    clean_name =secure_filename (filename )
    gallery_names ={"menuva.jpg","menuva1.jpg","menuva3.jpg","menuva4.jpg","menuva5.jpg"}
    flag_names ={
    "EUR.gif":"images/flags/eur.svg",
    "USD.gif":"images/flags/usd.svg",
    "GBP.gif":"images/flags/gbp.svg",
    "CHF.gif":"images/flags/chf.svg",
    "CAD.gif":"images/flags/cad.svg",
    "AUD.gif":"images/flags/aud.svg",
    }
    if clean_name in gallery_names :
        return redirect (url_for ("static",filename =f"images/gallery/{clean_name}"),code =301 )
    if clean_name in flag_names :
        return redirect (url_for ("static",filename =flag_names [clean_name]),code =301 )
    return redirect (url_for ("galerija"),code =301 )

@app .route ("/")
def index ():
    data =load_data ()
    return render_template ("index.html",data =data )


@app .route ("/локација")
@app .route ("/lokacija")
def lokacija ():
    return render_template ("lokacija.html",data =load_data ())


@app .route ("/en/location")
def en_lokacija ():
    session ["lang"]="en"
    return render_template ("lokacija.html",data =load_data ())


@app .route ("/галерија")
@app .route ("/galerija")
def galerija ():
    return render_template ("galerija.html",data =load_data ())


@app .route ("/en/gallery")
def en_galerija ():
    session ["lang"]="en"
    return render_template ("galerija.html",data =load_data ())


def get_public_base_url ():
    configured_url =os .environ .get ("SITE_URL",DEFAULT_SITE_URL ).strip ().rstrip ("/")
    if configured_url in LEGACY_SITE_URLS :
        configured_url =DEFAULT_SITE_URL
    if configured_url :
        return configured_url

    forwarded_proto =request .headers .get ("X-Forwarded-Proto",request .scheme ).split (",")[0 ].strip ()
    forwarded_host =request .headers .get ("X-Forwarded-Host",request .host ).split (",")[0 ].strip ()
    return f"{forwarded_proto}://{forwarded_host}".rstrip ("/")


def get_public_last_modified_date ():
    return datetime .now (SKOPJE_TZ ).date ().isoformat ()if SKOPJE_TZ else datetime .utcnow ().date ().isoformat ()


def normalize_public_endpoint (endpoint :str |None )->str :
    endpoint =endpoint or "index"
    return CANONICAL_ENDPOINTS .get (endpoint ,endpoint )


def build_localized_page_path (endpoint :str ,lang :str )->str :
    canonical_endpoint =normalize_public_endpoint (endpoint )
    return LOCALIZED_ROUTE_PATHS .get (canonical_endpoint ,LOCALIZED_ROUTE_PATHS ["index"]).get (lang ,"/")


def build_localized_page_url (endpoint :str ,lang :str )->str :
    return f"{get_public_base_url ()}{build_localized_page_path (endpoint ,lang )}"

def build_public_page_url (endpoint :str ,lang :str ="mk")->str :
    return build_localized_page_url (endpoint ,lang )


def build_alternate_urls (endpoint :str )->dict :
    canonical_endpoint =normalize_public_endpoint (endpoint )
    return {lang :build_localized_page_url (canonical_endpoint ,lang )for lang in SUPPORTED_LANGUAGES }


def build_canonical_url (endpoint :str |None =None ):
    endpoint =normalize_public_endpoint (endpoint or request .endpoint or "index")
    public_endpoints ={item [0 ]for item in PUBLIC_SITEMAP_PAGES }
    if endpoint not in public_endpoints :
        endpoint ="index"
    return build_public_page_url (endpoint ,get_current_language ())

def build_page_meta (site_data :dict ):
    endpoint =normalize_public_endpoint (request .endpoint or "index")
    current_lang =get_current_language ()
    ui =UI_TEXT [current_lang ]
    business_name =localized_value (site_data ["business"]["name"],current_lang )

    if endpoint =="kursna_lista":
        title ="Курсна листа денес - Менувачница ЕУРО МАРФИ Скопје"if current_lang =="mk"else "Exchange Rates Today - EURO MARFI Exchange Office Skopje"
        description =f"{business_name}: {localized_value (site_data ['business']['daily_info'],current_lang )}. Куповен и продажен курс за EUR, USD, GBP, CHF, CAD, AUD, RSD, BGN, TRY и ALB."if current_lang =="mk"else f"{business_name}: {localized_value (site_data ['business']['daily_info'],current_lang )}. Buy and sell rates for EUR, USD, GBP, CHF, CAD, AUD, RSD, BGN, TRY, and ALB."
    elif endpoint =="menuvacnica_skopje":
        title ="Менувачница Скопје - Курсна листа | ЕУРО МАРФИ"if current_lang =="mk"else "Exchange Office Skopje - Exchange Rates | EURO MARFI"
        description ="Менувачница Скопје со дневна курсна листа, куповен и продажен курс, работно време, телефон и локација. ЕУРО МАРФИ Скопје."if current_lang =="mk"else "Exchange office in Skopje with daily buy and sell rates, working hours, phone numbers, and location. EURO MARFI Skopje."
    elif endpoint =="menuvacnici_skopje":
        title ="Менувачници Скопје - Дневен курс | ЕУРО МАРФИ"if current_lang =="mk"else "Exchange Offices Skopje - Daily Rates | EURO MARFI"
        description ="Менувачници Скопје: проверете дневна курсна листа за EUR, USD, GBP, CHF и други валути, со директен контакт и адреса."if current_lang =="mk"else "Exchange offices in Skopje: check daily exchange rates for EUR, USD, GBP, CHF, and other currencies with direct contact and address."
    elif endpoint =="exchange_office_skopje":
        title ="Exchange Office Skopje - Daily Exchange Rates | EURO MARFI"if current_lang =="en"else "Менувачница Скопје - Курсна листа | ЕУРО МАРФИ"
        description ="EURO MARFI exchange office in Skopje with daily currency exchange rates, buy and sell table, working hours, phone numbers, and location."if current_lang =="en"else "Менувачница Скопје со дневна курсна листа, куповен и продажен курс, работно време, телефон и локација."
    elif endpoint =="lokacija":
        title =f"{ui ['nav_location']} | {business_name}"
        description =f"{business_name}: {site_data ['business']['address']}. {ui ['contact_text']}"
    elif endpoint =="galerija":
        title =f"{ui ['nav_gallery']} | {business_name}"
        description =SEO_GALLERY_DESCRIPTION [current_lang ]
    elif endpoint in NOINDEX_ENDPOINTS :
        title =f"{ui .get ('nav_admin','Admin')} | {business_name}"
        description ="Private administration page for the website owner."
    else :
        title =SEO_HOME_TITLE [current_lang ]
        description =SEO_HOME_DESCRIPTION [current_lang ]

    return {
    "title":title ,
    "description":description ,
    "canonical_url":build_canonical_url (endpoint ),
    "canonical_endpoint":endpoint ,
    "robots":"noindex, nofollow"if endpoint in NOINDEX_ENDPOINTS else "index, follow, max-image-preview:large",
    "image_url":f"{get_public_base_url ()}{url_for ('static',filename =SEO_IMAGE_FILENAME )}",
    "image_alt":f"{business_name} - {ui ['rates_title']}",
    "locale":"mk_MK"if current_lang =="mk"else "en_US",
    "alternate_locale":"en_US"if current_lang =="mk"else "mk_MK",
    }


def build_local_business_schema (site_data :dict ,page_meta :dict ):
    current_lang =get_current_language ()
    business =site_data ["business"]
    name =localized_value (business ["name"],"mk")or localized_value (business ["name"],"en")
    public_base_url =get_public_base_url ()
    canonical_url =page_meta ["canonical_url"]
    primary_phone =business .get ("phones",[""])[0 ]
    all_phones =[phone for phone in business .get ("phones",[])if phone ]
    currencies =[currency .get ("code","")for currency in site_data .get ("currencies",[])if currency .get ("code")]
    description =page_meta ["description"]
    faq_items =UI_TEXT [current_lang ].get ("faq_items",[])if page_meta .get ("canonical_endpoint") in {"index","kursna_lista","menuvacnica_skopje","menuvacnici_skopje","exchange_office_skopje"}else []
    graph =[
    {
    "@type":"FinancialService",
    "@id":f"{public_base_url}/#business",
    "name":name ,
    "alternateName":localized_value (business ["name"],"en"),
    "description":SEO_HOME_DESCRIPTION ["mk"],
    "url":public_base_url ,
    "telephone":primary_phone ,
    "contactPoint":[
    {
    "@type":"ContactPoint",
    "telephone":phone ,
    "contactType":"customer service",
    "areaServed":"MK",
    "availableLanguage":["mk","en"],
    }for phone in all_phones
    ],
    "image":page_meta ["image_url"],
    "logo":f"{public_base_url}{url_for ('static',filename ='favicon.svg')}",
    "priceRange":"$",
    "address":{
    "@type":"PostalAddress",
    "streetAddress":"ul. Hristo Tatarchev 33a",
    "addressLocality":"Skopje",
    "postalCode":"1000",
    "addressCountry":"MK",
    },
    "geo":{
    "@type":"GeoCoordinates",
    "latitude":41.97798415915381,
    "longitude":21.439950976565317,
    },
    "hasMap":"https://share.google/z7PZhCNkPWuyMizhk",
    "areaServed":[
    {"@type":"City","name":"Skopje"},
    {"@type":"Country","name":"North Macedonia"},
    ],
    "currenciesAccepted":", ".join (["MKD"]+currencies ),
    "paymentAccepted":"Cash",
    "openingHours":"Mo-Fr 09:00-16:00",
    "openingHoursSpecification":[
    {
    "@type":"OpeningHoursSpecification",
    "dayOfWeek":["Monday","Tuesday","Wednesday","Thursday","Friday"],
    "opens":"09:00",
    "closes":"16:00",
    }
    ],
    "knowsAbout":["Курсна листа","Менувачница","Куповен курс","Продажен курс","Foreign currency exchange"],
    },
    {
    "@type":"WebSite",
    "@id":f"{public_base_url}/#website",
    "url":public_base_url ,
    "name":name ,
    "inLanguage":["mk","en"],
    "publisher":{"@id":f"{public_base_url}/#business"},
    },
    {
    "@type":"WebPage",
    "@id":f"{canonical_url}#webpage",
    "url":canonical_url ,
    "name":page_meta ["title"],
    "description":description ,
    "inLanguage":current_lang ,
    "isPartOf":{"@id":f"{public_base_url}/#website"},
    "about":{"@id":f"{public_base_url}/#business"},
    "primaryImageOfPage":{
    "@type":"ImageObject",
    "url":page_meta ["image_url"],
    "caption":page_meta ["image_alt"],
    },
    },
    ]
    breadcrumb_items =[
    {
    "@type":"ListItem",
    "position":1,
    "name":"Home"if current_lang =="en"else "Почетна",
    "item":build_localized_page_url ("index",current_lang ),
    }
    ]
    if page_meta .get ("canonical_endpoint") !="index":
        breadcrumb_items .append ({
        "@type":"ListItem",
        "position":2,
        "name":page_meta ["title"].split ("|")[0 ].strip (),
        "item":canonical_url,
        })
    graph .append ({
    "@type":"BreadcrumbList",
    "@id":f"{canonical_url}#breadcrumb",
    "itemListElement":breadcrumb_items,
    })
    if faq_items:
        graph .append ({
        "@type":"FAQPage",
        "@id":f"{canonical_url}#faq",
        "mainEntity":[
        {
        "@type":"Question",
        "name":item ["question"],
        "acceptedAnswer":{"@type":"Answer","text":item ["answer"]},
        }for item in faq_items
        ],
        })
    return {"@context":"https://schema.org","@graph":graph}


@app .before_request
def redirect_legacy_domain ():
    forwarded_host =request .headers .get ("X-Forwarded-Host",request .host ).split (",")[0 ].strip ().split (":")[0 ].lower ()
    if forwarded_host in LEGACY_SITE_HOSTS :
        path =request .full_path if request .query_string else request .path
        return redirect (f"{DEFAULT_SITE_URL}{path}",code =301 )

@app .after_request
def apply_seo_headers (response ):
    if request .endpoint in NOINDEX_ENDPOINTS :
        response .headers ["X-Robots-Tag"]="noindex, nofollow"
    return response


@app .route ("/sitemap.xml")
def sitemap_xml ():
    last_modified =get_public_last_modified_date ()
    lines =[
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">',
    ]

    for endpoint ,change_frequency ,priority in PUBLIC_SITEMAP_PAGES :
        alternate_urls =build_alternate_urls (endpoint )
        for lang in SUPPORTED_LANGUAGES :
            page_url =build_public_page_url (endpoint ,lang )
            lines .extend ([
            "<url>",
            f"<loc>{xml_escape (page_url )}</loc>",
            *[f"<xhtml:link rel=\"alternate\" hreflang=\"{alternate_lang}\" href=\"{xml_escape (alternate_url )}\" />"for alternate_lang ,alternate_url in alternate_urls .items ()],
            f"<xhtml:link rel=\"alternate\" hreflang=\"x-default\" href=\"{xml_escape (build_public_page_url (endpoint ,'mk'))}\" />",
            f"<lastmod>{last_modified}</lastmod>",
            f"<changefreq>{change_frequency}</changefreq>",
            f"<priority>{priority}</priority>",
            "</url>",
            ])

    lines .append ("</urlset>")
    response =Response ("\n".join (lines ),mimetype ="application/xml")
    response .headers ["Cache-Control"]="public, max-age=3600"
    return response

@app .route ("/llms.txt")
def llms_txt ():
    base_url =get_public_base_url ()
    lines =[
    "# EURO MARFI",
    "",
    "EURO MARFI is a currency exchange office in Skopje, North Macedonia.",
    "The site publishes daily buy and sell exchange rates for EUR, USD, GBP, CHF, CAD, AUD, RSD, BGN, TRY, and ALB.",
    "",
    f"Homepage: {base_url}/",
    f"Exchange rates: {base_url}/kursna-lista",
    f"Location: {base_url}/lokacija",
    f"Gallery: {base_url}/galerija",
    f"Sitemap: {base_url}/sitemap.xml",
    "",
    "Admin, login, logout, and language-switching URLs are private or utility pages and should not be indexed.",
    ]
    return Response ("\n".join (lines ),mimetype ="text/plain")

@app .route ("/robots.txt")
def robots_txt ():
    lines =[
    "User-agent: *",
    "Allow: /",
    "Disallow: /admin",
    "Disallow: /logout",
    "Disallow: /set-language/",
    "",
    f"Sitemap: {get_public_base_url ()}/sitemap.xml",
    "",
    ]
    response =Response ("\n".join (lines ),mimetype ="text/plain")
    response .headers ["Cache-Control"]="public, max-age=3600"
    return response


@app .route ("/favicon.ico")
def favicon_ico ():
    return redirect (url_for ("static",filename ="favicon.svg"),code =301 )


@app .route ("/login",methods =["GET","POST"])
def login ():
    admin_settings =load_admin_settings ()

    if request .method =="GET"and is_logged_in ():
        return redirect (url_for ("admin"))

    if request .method =="POST":
        username =request .form .get ("username","").strip ()
        password =request .form .get ("password","").strip ()
        otp_code =request .form .get ("otp_code","").strip ().replace (" ","")

        if username !=admin_settings ["username"]or not check_password_hash (admin_settings ["password_hash"],password ):
            flash ("Погрешно корисничко име или лозинка.","error")
        elif admin_settings ["totp_enabled"]and not pyotp .TOTP (admin_settings ["totp_secret"]).verify (otp_code ,valid_window =1 ):
            flash ("Внесете валиден 2FA код од апликацијата за автентикација.","error")
        else :
            session .permanent =request .form .get ("remember_me")=="1"
            session ["admin_logged_in"]=True
            session ["admin_username"]=admin_settings ["username"]
            clear_pending_totp_secret ()
            flash ("Најавата е успешна. Сега можете да ја уредувате страницата.","success")
            return redirect (url_for ("admin"))

    return render_template ("login.html",totp_enabled =admin_settings ["totp_enabled"])


@app .route ("/logout")
def logout ():
    session .clear ()
    flash ("Успешно се одјавивте.","success")
    return redirect (url_for ("index"))


@app .route ("/admin",methods =["GET","POST"])
def admin ():
    if not is_logged_in ():
        flash ("Најавете се за пристап до административниот панел.","error")
        return redirect (url_for ("login"))

    data =load_data ()
    admin_settings =load_admin_settings ()

    if request .method =="POST":
        form_action =request .form .get ("form_action","save_content")

        if form_action =="save_content":
            save_data (update_site_data_from_admin_form (data ,request .form ,request .files ))
            flash ("Содржината е успешно ажурирана.","success")
        elif form_action =="change_password":
            current_password =request .form .get ("current_password","").strip ()
            new_password =request .form .get ("new_password","").strip ()
            confirm_password =request .form .get ("confirm_password","").strip ()

            if not check_password_hash (admin_settings ["password_hash"],current_password ):
                flash ("Тековната лозинка не е точна.","error")
            elif len (new_password )<8 :
                flash ("Новата лозинка треба да има најмалку 8 знаци.","error")
            elif new_password !=confirm_password :
                flash ("Новата лозинка и потврдата не се совпаѓаат.","error")
            else :
                admin_settings ["password_hash"]=generate_password_hash (new_password )
                save_admin_settings (admin_settings )
                flash ("Лозинката е успешно променета.","success")
        elif form_action =="enable_2fa":
            current_password =request .form .get ("enable_2fa_password","").strip ()
            otp_code =request .form .get ("enable_2fa_code","").strip ().replace (" ","")
            pending_secret =get_pending_totp_secret ()

            if not check_password_hash (admin_settings ["password_hash"],current_password ):
                flash ("Внесете ја точната тековна лозинка за да активирате 2FA.","error")
            elif not pyotp .TOTP (pending_secret ).verify (otp_code ,valid_window =1 ):
                flash ("Внесете валиден код од апликацијата за автентикација.","error")
            else :
                admin_settings ["totp_enabled"]=True
                admin_settings ["totp_secret"]=pending_secret
                save_admin_settings (admin_settings )
                clear_pending_totp_secret ()
                flash ("2FA е успешно активирана.","success")
        elif form_action =="disable_2fa":
            current_password =request .form .get ("disable_2fa_password","").strip ()

            if not check_password_hash (admin_settings ["password_hash"],current_password ):
                flash ("Внесете ја точната лозинка за да ја исклучите 2FA.","error")
            else :
                admin_settings ["totp_enabled"]=False
                admin_settings ["totp_secret"]=""
                save_admin_settings (admin_settings )
                clear_pending_totp_secret ()
                flash ("2FA е исклучена.","success")

        return redirect (url_for ("admin"))

    totp_setup_secret =""
    totp_qr_svg =""
    totp_setup_uri =""

    if not admin_settings ["totp_enabled"]:
        totp_setup_secret =get_pending_totp_secret ()
        totp_qr_svg ,totp_setup_uri =build_totp_setup_payload (admin_settings ["username"],totp_setup_secret )

    rate_date_value =datetime .now ().strftime ("%Y-%m-%d")
    stored_rate_date =re .search (r"(\d{2})\.(\d{2})\.(\d{4})",localized_value (data ["business"].get ("daily_info"),"mk"))
    if stored_rate_date :
        rate_date_value =f"{stored_rate_date .group (3)}-{stored_rate_date .group (2)}-{stored_rate_date .group (1)}"

    return render_template (
    "admin.html",
    data =data ,
    rate_date_value =rate_date_value ,
    admin_settings =admin_settings ,
    totp_setup_secret =totp_setup_secret ,
    totp_qr_svg =totp_qr_svg ,
    totp_setup_uri =totp_setup_uri ,
    )


if __name__ =="__main__":
    ensure_data_file ()
    ensure_admin_settings ()
    app .run (debug =True )
