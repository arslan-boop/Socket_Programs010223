from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

def my_multithreading_method(my_list, lock):
    with lock:
        my_list.append("Hello")
        return True

lock = Lock()

def parallel_execution(my_list):
    try:
        response_list = []
        future_list = []
        list_count = len(my_list)
        with ThreadPoolExecutor(max_workers=list_count) as executor:
            for index in range(list_count):
                future_list.append(executor.submit(my_multithreading_method, my_list[index], lock))
            for future in as_completed(future_list):
                return_value = future.result()
                response_list.append(return_value[0])
        return response_list
    except Exception as error:
        raise Exception(str(error))