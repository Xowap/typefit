from typing import Text

try:
    import pendulum
except ImportError:
    pass
else:
    # noinspection PyInitNewSignature
    class DateTimeFit(pendulum.DateTime):
        """
        Parses a date/time and returns a standard pendulum DateTime.
        """

        def __new__(cls, date: Text):
            self = pendulum.parse(date)

            if not isinstance(self, pendulum.DateTime):
                raise ValueError

            return self

    # noinspection PyInitNewSignature
    class TimeStampFit(pendulum.DateTime):
        """
        Parses a Unix timestamp and returns a standard pendulum DateTime.
        """

        def __new__(cls, date: int):
            return pendulum.from_timestamp(date)

    # noinspection PyInitNewSignature
    class DateFit(pendulum.Date):
        """
        Parses a date and returns a standard pendulum Date.
        """

        def __new__(cls, date: Text):
            self = pendulum.parse(date)

            if isinstance(self, pendulum.DateTime):
                self = self.date()

            if not isinstance(self, pendulum.Date):
                raise ValueError

            return self
