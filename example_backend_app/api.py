"""Example backend app API"""


class ExampleAPI:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def hello(self):
        return 'Hello world from example_backend_app! (kwargs: {})'.format(
            self.kwargs
        )
