from PyQt5.QtCore import QRunnable, pyqtSlot, QThreadPool

ThreadPool = QThreadPool()

class Job(QRunnable):

    def __init__(self, fn, *args, **kwargs):
        super(Job, self).__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        self.fn(*self.args, **self.kwargs)