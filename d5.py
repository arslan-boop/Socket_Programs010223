import threading, queue

q = queue.Queue()
liste = ['Ankara', 'İstanbul', 'Kayseri']

def islem1():
    global liste
    while not q.empty():
        item = q.get()
        print(f"Çıkarılacak eleman: {item}")
        q.task_done()

def islem():
    global liste
    for i in liste:
        q.put(i)
        print('kuyruk', q.queue)

if __name__ == '__main__':
    islem()
    print('işlem sonrası kuyruk', q.queue)
    islem1()
