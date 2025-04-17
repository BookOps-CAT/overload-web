import abc
from typing import Union

from overload_web.domain import model


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def get(self, id: Union[str, int]) -> model.Template:
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, template: model.Template):
        raise NotImplementedError


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def get(self, id: Union[str, int]):
        return self.session.query(model.Template).filter_by(id=id).first()

    def save(self, template: model.Template) -> None:
        self.session.add(template)
