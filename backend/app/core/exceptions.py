class DataIncompleteError(Exception):
    """Raised when critical data is missing for analysis."""
    def __init__(self, message: str, missing_fields: list = None):
        super().__init__(message)
        self.missing_fields = missing_fields or []
