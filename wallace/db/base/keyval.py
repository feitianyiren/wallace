from contextlib import contextmanager
import uuid

from wallace.db.base.errors import DoesNotExist, ValidationError
from wallace.db.base.model import Model


class KeyValueModel(Model):

    @classmethod
    def fetch(cls, ident):
        inst = cls()
        inst._set_db_key(ident)
        inst.pull()
        return inst

    @classmethod
    def construct(cls, ident=None, new=True, **kwargs):
        if not new and ident is None:
            raise ValidationError('must pass ident')

        inst = super(KeyValueModel, cls).construct(new=new, **kwargs)

        if not new:
            inst._set_db_key(ident)

        return inst

    def __init__(self):
        Model.__init__(self)
        self._cbs_db_key = None

    @property
    def db_key(self):
        if self._cbs_db_key is None:
            raise DoesNotExist('new model')
        return self._cbs_db_key


    _create_new_ident = staticmethod(lambda: uuid.uuid4().hex)
    prefix = None

    @classmethod
    def _format_db_key(cls, ident):
        return '%s:%s' % (cls.prefix, ident,) if cls.prefix else ident

    def _set_db_key(self, ident):
        self._cbs_db_key = self._format_db_key(ident)


    @contextmanager
    def _new_model_key_handler(self):
        reset_key_on_error = False
        if self.is_new:
            self._set_db_key(self._create_new_ident())
            reset_key_on_error = True

        try:
            yield
        except:
            if reset_key_on_error:
                # todo may make sense to do an existence check here (or catch
                # a more specific error) so we don't end up with orphaned items
                self._cbs_db_key = None
            raise

    def push(self, *a, **kw):
        with self._new_model_key_handler():
            super(KeyValueModel, self).push(*a, **kw)