from PyQt6.QtCore import QObject, pyqtSignal, QRunnable, QThreadPool

class WorkerSignals(QObject):
    """
    Defines the signals available from a running worker thread.
    Supported signals are:
    - finished: No data
    - error: tuple (exctype, value, traceback.format_exc())
    - result: object data returned from processing
    """
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)

class Worker(QRunnable):
    """
    Worker thread that can run any function with given args and kwargs.
    """
    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        """
        Execute the function in the background.
        """
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            import traceback
            exctype = type(e)
            self.signals.error.emit((exctype, str(e), traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()