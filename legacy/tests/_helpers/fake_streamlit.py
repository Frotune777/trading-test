# tests/_helpers/fake_streamlit.py
class FakeStreamlit:
    def __getattr__(self, name):
        def _noop(*args, **kwargs):
            return None
        return _noop

st = FakeStreamlit()
