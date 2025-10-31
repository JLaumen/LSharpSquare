class DCValue:
    def __init__(self, value=None):
        self.value = value

    def is_known(self):
        return self.value is not None

    def __eq__(self, other):
        if not isinstance(other, DCValue):
            return False
        if not self.is_known() or not other.is_known():
            return True
        return self.value == other.value