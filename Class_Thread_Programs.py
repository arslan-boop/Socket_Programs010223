from time import sleep
from threading import Thread

# custom thread
class CustomThread(Thread):
    # constructor
    def __init__(self):
        # execute the base constructor
        Thread.__init__(self)
        # set a default value
        self.value = None
        self.run()
    # function executed in a new thread
    def run(self):
        # block for a moment
        sleep(1)
        # store data in an instance variable
        self.value = 'Hello from a new thread'
    def run1(self):
        # block for a moment
        sleep(1)
        # store data in an instance variable
        self.value11 = 'Hello fr thread'



if __name__ == "__main__":
    i = 1
    while (True):
        try:
            # create a new thread
            thread = CustomThread()
            thread.start()
            data = thread.value
            print('data',data,i)

            thread = CustomThread()
            thread.start()
            data = thread.value
            print('data',data,i)


        except Exception as exp:
            v_hata_mesaj = 'Hata Oluştu!!..T1  = ' + str(exp)
            print('csd')

"""
from time import sleep
from threading import Thread

# custom thread
class CustomThread(Thread):
    # constructor
    def __init__(self):
        # execute the base constructor
        Thread.__init__(self)
        # set a default value
        self.value = None
        self.run()
    # function executed in a new thread
    def run(self):
        # block for a moment
        sleep(1)
        # store data in an instance variable
        self.value = 'Hello from a new thread'

# create a new thread
thread = CustomThread()
# start the thread
thread.start()
# wait for the thread to finish
#thread.join()
# get the value returned from the thread
data = thread.value
print(data)
"""