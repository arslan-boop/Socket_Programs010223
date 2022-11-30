"""
  In order to print result array elements, we use result[:] to print complete array.
    print("Result(in process p1): {}".format(result[:]))
  # Server process : Whenever a python program starts, a server process is also started. From there on, whenever a
  new process is needed, the parent process connects to the server and requests it to fork a new process.
  # A server process can hold Python objects and allows other processes to manipulate them using proxies.
  # multiprocessing module provides a Manager class which controls a server process. Hence, managers provide a
  way to create data that can be shared between different processes.

  Server process managers are more flexible than using shared memory objects because they can be made to
   support arbitrary object types like lists, dictionaries, Queue, Value, Array, etc. Also, a single manager
   can be shared by processes on different computers over a network. They are, however, slower than using shared memory.

  """
# SuperFastPython.com
# example of shared ctypes for a string
from multiprocessing import Array ,Value
from multiprocessing import Process
import multiprocessing

v_last = 0
v_dizi = []
v_dizichar = []

# function to execute in a child process
def task(variable, v2dizi,su,dizichar):
    #-------
    data = b'Hello!'
    su.value = son()
    v1,v2 = sndiz()
    v2dizi.value=v1
    dizichar.value =v2
    variable.value = data
    # -------

def son():
    global  v_last
    v_last = 60000
    return v_last

def sndiz():
    global  v_dizi, v_dizichar
    v_dizi.append(77)
    v_dizi.append(99)
    #return v_dizi[0], v_dizi[1]
    v_dizichar.append('ETCUSDT')
    v_dizichar.append('BTCUSDT')

    return v_dizi, v_dizichar


def square_list(mylist, result, square_sum):
    # append squares of mylist to result array
    for idx, num in enumerate(mylist):
        result[idx] = num * num
    # square_sum value
    square_sum.value = sum(result)
    # print result Array
    print("Result(in process p1): {}".format(result[:]))
    # print square_sum Value
    print("Sum of squares(in process p1): {}".format(square_sum.value))

# protect the entry point
if __name__ == '__main__':
    # input list
    mylist = [1, 2, 3, 4]
    # creating Array of int data type with space for 4 integers
    result = multiprocessing.Array('i', 4)
    # creating Value of int data type
    square_sum = multiprocessing.Value('i')
    #square_sum = multiprocessing.Value('i', 10) başlangıç değeri verebiliriz.
    #p1 = Process(target=square_list, args=(mylist, result, square_sum))
      # create shared variable
    su = Value('d', 0.0)
    variable = Array('c', b'Hello World')
    v2dizi = Array('i', range(2))
    dizichar = Array('b', range(2))

    process = Process(target=task, args=(variable,v2dizi,su,dizichar))
    process.start()
    process.join()

    data = variable.value
    dasu = su.value
    dadiz =  v2dizi[:]
    dadic = dizichar[:]

    print('data', f'Read: {data}')
    print('dasuuu', f'Read: {dasu}')
    print('Dizi',f'Read: {dadiz}')
    print('Dizi2',f'Read: {dadic}')