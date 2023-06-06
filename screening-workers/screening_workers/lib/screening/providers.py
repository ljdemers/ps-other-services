from screening_api.ships.models import Ship

from screening_workers.screenings_profiles.models import (
    DefaultScreeningProfile as ScreeningProfile,
)


class DataProvider:
    """
    Data store for check prerequisites.

    Any values required by a screening check should be gathered up and stored
    in one of these objects.
    """

    def __init__(self, screening, **kwargs):
        self.screening = screening

        self.update(**kwargs)

    @property
    def ship(self) -> Ship:
        return self.screening.ship

    @property
    def screening_profile(self) -> ScreeningProfile:
        # @todo: implement account profiles
        return ScreeningProfile

    def update(self, **kwargs):
        self.__dict__.update(kwargs)
