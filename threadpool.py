from threading import Thread
from logging import getLogger
from six.moves.queue import Queue
from threading import Lock
import gc
import time


class WorkerThread(Thread):
    def __init__(self, task_queue, *args, **kwargs):
        super(WorkerThread, self).__init__(*args, **kwargs)

        self._task_queue = task_queue
        self._succ_task_num = 0
        self._fail_task_num = 0
        self._ret = list()

    def run(self):
        while True:
            func, args, kwargs = self._task_queue.get()

            try:
                ret = func(*args, **kwargs)
                self._succ_task_num += 1
                self._ret.append(ret)

            except Exception as e:
                print(e)
                self._fail_task_num += 1
                self._ret.append(e)
            finally:
                self._task_queue.task_done()
            if self._task_queue.empty():
                break

    def get_result(self):
            return self._succ_task_num, self._fail_task_num, self._ret


class SimpleThreadPool:

    def __init__(self, num_threads=5):
        self._num_threads = num_threads
        self._queue = Queue(2000)
        self._lock = Lock()
        self._active = False
        self._workers = list()
        self._finished = False

    def add_task(self, func, *args, **kwargs):
        if not self._active:
            with self._lock:
                if not self._active:
                    self._active = True
                    for i in range(self._num_threads):
                        w = WorkerThread(self._queue)
                        self._workers.append(w)
                        w.start()

        self._queue.put((func, args, kwargs))

    def release(self):
        while self._queue.empty() is False:
            time.sleep(1)

    def wait_completion(self):
        self._queue.join()
        self._finished = True

    def get_result(self):
        assert self._finished
        detail = [worker.get_result() for worker in self._workers]
        succ_all = all([tp[1] == 0 for tp in detail])
        return {'success_all': succ_all, 'detail': detail}


if __name__ == '__main__':

    pool = SimpleThreadPool(2)