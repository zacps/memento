class Metric(object):
    _instance = None

    # Creates a singleton, without having to call a .get_instance() method
    # Can just call obj = Metric() like normal, but will always create 1 instance
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Metric, cls).__new__(cls)
            cls._setup(cls)
        return cls._instance

    def _setup(self):
        pass
