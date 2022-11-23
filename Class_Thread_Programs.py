from datetime import datetime
from time import sleep
from threading import Thread

# custom thread
class CustomThread():
    # constructor
    def __init__(self, message1):
        # execute the base constructor
        #Thread.__init__(self)
        # set a default value
        self.run(message1)
        #print('fsdf', message1)
    # function executed in a new thread
    def run(self,v_mess):
        # block for a moment
        sleep(1)
        # store data in an instance variable
        self.value = v_mess


if __name__ == "__main__":
    print('Başladı')
    with open('Sembol3.txt', 'r') as dosya:
        for line in dosya.read().splitlines():
            #print(line)
            v_symbol = line
            thread = CustomThread(v_symbol)
            data = thread.value
            print('data',data,datetime.now())
