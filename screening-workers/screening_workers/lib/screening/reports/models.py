from screening_api.screenings.enums import Severity


class Report(dict):

    @property
    def severity(self) -> Severity:
        raise NotImplementedError

    def asdict(self) -> dict:
        raise NotImplementedError

    def __setitem__(self, key, value):
        return super(Report, self).__setitem__(key, value)

    def __getitem__(self, name):
        return super(Report, self).__getitem__(name)

    __getattr__ = __getitem__
    __setattr__ = __setitem__
