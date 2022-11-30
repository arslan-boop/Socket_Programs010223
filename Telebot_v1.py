import requests
from datetime import datetime
def mainma(mess):
    TOKEN = "5789458481:AAHzXw9nTTrG6Lu8ieOz1LUl4e7J-TJrTfU"
    chat_id = "1372025054"
    message = mess
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    print(requests.get(url).json())

def kar_zarar_durumu(mess):
    TOKEN = "5789458481:AAHzXw9nTTrG6Lu8ieOz1LUl4e7J-TJrTfU"
    chat_id = "1372025054"
    message = mess
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    #print(requests.get(url).json())

    with open("Sonuc.txt", "a" , encoding="utf-8") as f:
        #f.write("\n"+message)
        f.write(message+"\n")
        #f.write(message)
        f.close()
def dosyalari_temizle():
    open("Alinanlar.txt", 'w').close()
    open("Satilanlar.txt", 'w').close()

def genel_alimlar(v_sembol,v_tip):
    if v_tip == 'A':
        with open("Alinanlar.txt", "a", encoding="utf-8") as f:
            # f.write("\n"+message)
            f.write(v_sembol + "\n")
            # f.write(message)
            f.close()
    else:
        with open("Satilanlar.txt", "a", encoding="utf-8") as f:
            # f.write("\n"+message)
            f.write(v_sembol + "\n")
            # f.write(message)
            f.close()

if __name__ == '__main__':
    mainma("selam")
    mainma("selam")
    mainma("selamweqweqw")
