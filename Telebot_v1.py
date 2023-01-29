import requests
import time
from datetime import datetime
def mainma(mess,v_program_tip):
    TOKEN = "5789458481:AAHzXw9nTTrG6Lu8ieOz1LUl4e7J-TJrTfU"
    chat_id = "1372025054"
    message = "ProgramTip="+ str(v_program_tip)+'-'+ str(mess)
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    print(requests.get(url).json())

def analiz(mess,v_sembol):
    v_dosya = "OLD/"+str(datetime.now())[0:10]+str(v_sembol)+".txt"
    with open(v_dosya, "a" , encoding="utf-8") as f:
        #f.write("\n"+message)
        f.write(mess+"\n")
        #f.write(message)
        f.close()
def analiz_islem_log(mess,v_sembol):
    v_dosya = "OLD/LOG/"+str(datetime.now())[0:10]+str(v_sembol)+".txt"
    with open(v_dosya, "a" , encoding="utf-8") as f:
        #f.write("\n"+message)
        f.write(mess+"\n")
        #f.write(message)
        f.close()
def analiz_dk(mess,v_sembol):
    v_dosya = "OLD/"+"DK_"+str(datetime.now())[0:10]+str(v_sembol)+".txt"
    with open(v_dosya, "a" , encoding="utf-8") as f:
        #f.write("\n"+message)
        f.write(mess+"\n")
        #f.write(message)
        f.close()
def kar_zarar_durumu(mess,v_dosya_sonuc):
    TOKEN = "5789458481:AAHzXw9nTTrG6Lu8ieOz1LUl4e7J-TJrTfU"
    chat_id = "1372025054"
    message = mess
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={chat_id}&text={message}"
    #print(requests.get(url).json())

    with open(v_dosya_sonuc, "a" , encoding="utf-8") as f:
        #f.write("\n"+message)
        f.write(message+"\n")
        #f.write(message)
        f.close()
def dosyalari_temizle( v_dosya_alinan,v_dosya_satilan):
    open(v_dosya_alinan, 'w').close()
    open(v_dosya_satilan, 'w').close()

def islenen_coinler(v_dosya_islenen,v_sembol):
    with open(v_dosya_islenen, "a", encoding="utf-8") as f:
        # f.write("\n"+message)
        f.write(v_sembol + "\n")
        # f.write(message)
        f.close()
def acil_dosyasina_yaz(v_dosya_islenen,v_sembol):
    with open(v_dosya_islenen, "a", encoding="utf-8") as f:
        # f.write("\n"+message)
        f.write(v_sembol + "\n")
        # f.write(message)
        f.close()
def genel_alimlar(v_sembol,v_tip,v_dosya_genelbuy, v_dosya_alinan,v_dosya_satilan,v_dosya_sabika):
    if v_tip == 'A':
        with open(v_dosya_alinan, "a", encoding="utf-8") as f:
            # f.write("\n"+message)
            f.write(v_sembol + "\n")
            # f.write(message)
            f.close()
    elif v_tip == 'S':
        with open(v_dosya_satilan, "a", encoding="utf-8") as f:
            # f.write("\n"+message)
            f.write(v_sembol + "\n")
            # f.write(message)
            f.close()
        """
        with open(v_dosya_sabika, "a", encoding="utf-8") as f:
            # Cezası 4 saat sonra dolacak
            current_timestamp = round(time.time() * 1000)
            v_ceza_bitim_tar = (current_timestamp + (14400000)) / 1000
            v_ceza_bitim_tar = int(v_ceza_bitim_tar)
            # print(str(v_sembol))
            # print(str(v_ceza_bitim_tar))
            # print(str(datetime.now()))
            v_mess = str(v_sembol) + '*' + str(v_ceza_bitim_tar)+ '*' + str(datetime.now())
            print(v_mess)
            f.write(v_mess + "\n")
            # f.write(message)
            f.close()
        """
        with open(v_dosya_genelbuy, "a", encoding="utf-8") as f:
            # f.write("\n"+message)
            v_mess1 = str(v_sembol) +'*'+str(datetime.now())
            f.write(v_mess1 + "\n")
            # f.write(message)
            f.close()
def sabikali_yap(v_sembol,v_dosya_sabika,v_sabika_sure):
    #print('selam')
       with open(v_dosya_sabika, "a", encoding="utf-8") as f:
            # Cezası 4 saat sonra dolacak
            current_timestamp = round(time.time() * 1000)
            v_ceza_bitim_tar = (current_timestamp + (60000*v_sabika_sure)) / 1000
            v_ceza_bitim_tar = int(v_ceza_bitim_tar)
            # print(str(v_sembol))
            # print(str(v_ceza_bitim_tar))
            # print(str(datetime.now()))
            v_mess = str(v_sembol) + '*' + str(v_ceza_bitim_tar)+ '*' + str(datetime.now())
            print(v_mess)
            f.write(v_mess + "\n")
            # f.write(message)
            f.close()
if __name__ == '__main__':
    mainma("selam")
    mainma("selam")
    mainma("selamweqweqw")
