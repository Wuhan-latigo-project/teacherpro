from PySide6.QtCore import QRunnable, QObject, Signal
import config

class WorkerSignals(QObject):
    """Signals for worker threads"""
    finished = Signal()
    error = Signal(str)
    result = Signal(object)
    progress = Signal(int)

class ApiWorker(QRunnable):
    """Worker thread for API calls"""
    def __init__(self, function, *args, **kwargs):
        super().__init__()
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        
    def run(self):
        """Run the worker task"""
        try:
            result = self.function(*self.args, **self.kwargs)
            self.signals.result.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))
        finally:
            self.signals.finished.emit()