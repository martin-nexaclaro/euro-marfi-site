from __future__ import annotations 

import io
import json
import re
import uuid
from copy import deepcopy
from datetime import datetime ,time
from pathlib import Path

try :
    from zoneinfo import ZoneInfo ,ZoneInfoNotFoundError 
except ImportError :
    ZoneInfo =None 
    ZoneInfoNotFoundError =Exception 

import pyotp 
import qrcode 
from flask import Flask ,flash ,redirect ,render_template ,request ,session ,url_for 
from qrcode .image .svg import SvgPathImage 
from werkzeug.security import check_password_hash ,generate_password_hash
from werkzeug.utils import secure_filename

app =Flask (__name__ )
app .config ["SECRET_KEY"]="change-this-secret-key-before-production"

# Change this starter username later for the real owner/admin login.
# The password is now stored as a secure hash in data/admin_settings.json
# and can be changed from inside the admin panel.
ADMIN_USERNAME ="admin"
ADMIN_PASSWORD ="changeme123"

BASE_DIR =Path (__file__ ).resolve ().parent
DATA_FILE =BASE_DIR /"data"/"site_data.json"
ADMIN_SETTINGS_FILE =BASE_DIR /"data"/"admin_settings.json"
GALLERY_DIR =BASE_DIR /"static"/"images"/"gallery"
VIDEO_DIR =BASE_DIR /"static"/"videos"
SUPPORTED_LANGUAGES =("mk","en")
_GALLERY_ALLOWED_EXTENSIONS ={"jpg","jpeg","png","webp","gif"}
_VIDEO_ALLOWED_EXTENSIONS ={"mp4","webm","mov","avi","mkv"}

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
"call_label":"Јавете се",
"moneygram_title":"MoneyGram трансфер услуги",
"moneygram_text":"Во менувачницата е достапна и услуга за MoneyGram парични трансфери.",
"location_eyebrow":"Локација",
"location_title":"Посетете нè",
"location_link":"Отвори локација",
"counter_eyebrow":"Посетители",
"counter_text":"Едноставен бројач на посети зачуван локално во постоечката JSON датотека.",
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
"call_label":"Call now",
"moneygram_title":"MoneyGram Transfer Services",
"moneygram_text":"The exchange office also supports MoneyGram money transfer services.",
"location_eyebrow":"Location",
"location_title":"Visit Us",
"location_link":"Open location page",
"counter_eyebrow":"Visitors",
"counter_text":"A simple visit counter stored locally in the existing JSON file.",
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
"title":{"mk":"Менувачница","en":"Exchange Office"},
"description":{
"mk":"Р¤РѕС‚РѕРіСЂР°С„РёСР° РѕРґ РјРµРЅСѓРІР°С‡РЅРёС†Р°С‚Р°.",
"en":"Photo of the exchange office.",
},
},
{
"image":"images/gallery/menuva1.jpg",
"title":{"mk":"Услужен простор","en":"Service Area"},
"description":{
"mk":"Р¤РѕС‚РѕРіСЂР°С„РёСР° РѕРґ РІРЅР°С‚СЂРµС€РЅРёРѕС‚ РїСЂРѕСЃС‚РѕСЂ.",
"en":"Photo of the interior area.",
},
},
{
"image":"images/gallery/menuva4.jpg",
"title":{"mk":"Р›РѕРєР°С†РёСР°","en":"Location"},
"description":{
"mk":"Р¤РѕС‚РѕРіСЂР°С„РёСР° РѕРґ РѕР±СРµРєС‚РѕС‚ Рё РѕРєРѕР»РёРЅР°С‚Р°.",
"en":"Photo of the office and surroundings.",
},
},
{
"image":"images/gallery/menuva.jpg",
"title":{"mk":"Простор","en":"Office Space"},
"description":{
"mk":"Дополнителен поглед од менувачницата.",
"en":"Additional view of the exchange office.",
},
},
{
"image":"images/gallery/menuva3.jpg",
"title":{"mk":"Ентериер","en":"Interior"},
"description":{
"mk":"Р¤РѕС‚РѕРіСЂР°С„РёСР° РѕРґ РµРЅС‚РµСЂРёРµСЂРѕС‚.",
"en":"Photo of the interior.",
},
},
],
"visitor_count":0 ,
}


def ensure_data_file ()->None :
    DATA_FILE .parent .mkdir (parents =True ,exist_ok =True )
    if not DATA_FILE .exists ():
        save_data (deepcopy (DEFAULT_DATA ))


def default_admin_settings ()->dict :
    return {
    "username":ADMIN_USERNAME ,
    "password_hash":generate_password_hash (ADMIN_PASSWORD ),
    "totp_enabled":False ,
    "totp_secret":"",
    }


def save_admin_settings (settings :dict )->None :
    ADMIN_SETTINGS_FILE .parent .mkdir (parents =True ,exist_ok =True )
    with ADMIN_SETTINGS_FILE .open ("w",encoding ="utf-8")as file :
        json .dump (settings ,file ,indent =2 ,ensure_ascii =False )


def ensure_admin_settings ()->None :
    ADMIN_SETTINGS_FILE .parent .mkdir (parents =True ,exist_ok =True )
    if not ADMIN_SETTINGS_FILE .exists ():
        save_admin_settings (default_admin_settings ())


def load_admin_settings ()->dict :
    ensure_admin_settings ()
    with ADMIN_SETTINGS_FILE .open ("r",encoding ="utf-8")as file :
        current_settings =json .load (file )

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
    with DATA_FILE .open ("r",encoding ="utf-8")as file :
        data =json .load (file )

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

    data ["visitor_count"]=int (data .get ("visitor_count",0 ))
    return data 


def save_data (data :dict )->None :
    DATA_FILE .parent .mkdir (parents =True ,exist_ok =True )
    with DATA_FILE .open ("w",encoding ="utf-8")as file :
        json .dump (data ,file ,indent =2 ,ensure_ascii =False )


def save_gallery_image (file_storage )->str :
    original =secure_filename (file_storage .filename or "")
    ext =original .rsplit (".",1 )[-1 ].lower ()if "."in original else ""
    if ext not in _GALLERY_ALLOWED_EXTENSIONS :
        return ""
    GALLERY_DIR .mkdir (parents =True ,exist_ok =True )
    unique_name =f"{uuid .uuid4 ().hex }.{ext }"
    file_storage .save (GALLERY_DIR /unique_name )
    return f"images/gallery/{unique_name }"


def save_gallery_video (file_storage )->str :
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
    if not session .get ("visit_counted"):
        data ["visitor_count"]=int (data .get ("visitor_count",0 ))+1 
        save_data (data )
        session ["visit_counted"]=True 
    return int (load_data ().get ("visitor_count",0 ))


def update_site_data_from_admin_form (data :dict ,form ,files =None )->dict :
    data ["business"]["daily_info"]={
    "mk":form .get ("daily_info_mk","").strip (),
    "en":form .get ("daily_info_en","").strip (),
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


@app .template_filter ("highlight_date")
def highlight_date_filter (value :str )->str :
    return re .sub (r"(\d{2}\.\d{2}\.\d{4})",r'<strong class="date-accent">\1</strong>',value )


@app .context_processor
def inject_site_data ():
    current_lang =get_current_language ()
    site_data =load_data ()
    return {
    "site_data":site_data ,
    "current_lang":current_lang ,
    "ui":UI_TEXT [current_lang ],
    "business_status":get_business_status (site_data ["business"]["working_hours"]),
    "text_for":lambda value :localized_value (value ,current_lang ),
    }


@app .route ("/set-language/<lang>")
def set_language (lang :str ):
    if lang in SUPPORTED_LANGUAGES :
        session ["lang"]=lang 
    next_url =request .args .get ("next")or url_for ("index")
    return redirect (next_url )


@app .route ("/")
def index ():
    visitor_count =increment_visitor_count ()
    data =load_data ()
    return render_template ("index.html",data =data ,visitor_count =visitor_count )


@app .route ("/lokacija")
def lokacija ():
    return render_template ("lokacija.html",data =load_data ())


@app .route ("/galerija")
def galerija ():
    return render_template ("galerija.html",data =load_data ())


@app .route ("/login",methods =["GET","POST"])
def login ():
    admin_settings =load_admin_settings ()

    if request .method =="POST":
        username =request .form .get ("username","").strip ()
        password =request .form .get ("password","").strip ()
        otp_code =request .form .get ("otp_code","").strip ().replace (" ","")

        if username !=admin_settings ["username"]or not check_password_hash (admin_settings ["password_hash"],password ):
            flash ("Погрешно корисничко име или лозинка.","error")
        elif admin_settings ["totp_enabled"]and not pyotp .TOTP (admin_settings ["totp_secret"]).verify (otp_code ,valid_window =1 ):
            flash ("Внесете валиден 2FA код од апликацијата за автентикација.","error")
        else :
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

    return render_template (
    "admin.html",
    data =data ,
    admin_settings =admin_settings ,
    totp_setup_secret =totp_setup_secret ,
    totp_qr_svg =totp_qr_svg ,
    totp_setup_uri =totp_setup_uri ,
    )


if __name__ =="__main__":
    ensure_data_file ()
    ensure_admin_settings ()
    app .run (debug =True )
