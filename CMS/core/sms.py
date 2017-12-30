from urllib.parse import urlencode
from urllib.request import Request, urlopen


def send_sms(recipient, text):
    url = 'https://lcab.smsintel.ru/lcabApi/sendSms.php'
    post_fields = {
        'login': '89068734350',
        'password': 'pg2vy',
        'txt': text,
        'to': recipient,
        'source': 'ООО "ПКФ Питон"',
    }
    sms_request = Request(url, urlencode(post_fields).encode())
    print(sms_request)
    sms_response = urlopen(sms_request).read().decode('unicode_escape')
    print(sms_response)
