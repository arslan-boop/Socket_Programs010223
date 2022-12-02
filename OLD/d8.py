import multiprocessing
import threading, queue

quyruk =queue.Queue()
dizi = []

def square_list(mylist, q):
	global quyruk, dizi

	for num in mylist:
		q.put(num * num)
		quyruk.put(num * num)
	dizi.append('44')
	print('quy',quyruk.queue )
	print('buy', dizi)
	return dizi

def print_queue(q):
	#print("Queue elements:")
	# while not q.empty():
	# 	print(q.get())
	c=1
	#print("Queue is now empty!")

if __name__ == "__main__":
	#global dizi
	# input list
	mylist = [1,2,3,4]
	# creating multiprocessing Queue
	q = multiprocessing.Queue()

	# creating new processes
	p1 = multiprocessing.Process(target=square_list, args=(mylist, q))

	p2 = multiprocessing.Process(target=print_queue, args=(q,))

	# running process p1 to square list
	p1.start()
	p1.join()

	# running process p2 to get queue elements
	p2.start()
	p2.join()

	v= square_list(mylist, q)
	#print('quyloo', quyruk.queue)
	print('Dizii', v)

	print('Kuyruk son', q)