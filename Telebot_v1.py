import requests
def mainma(mess):
    TOKEN = "5789458481:AAHzXw9nTTrG6Lu8ieOz1LUl4e7J-TJrTfU"
    chat_id = "1372025054"
    message =  mess
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    print(requests.get(url).json())
if __name__ == '__main__':
    mainma("selam")