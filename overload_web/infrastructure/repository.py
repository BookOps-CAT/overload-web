from typing import Protocol, Union, runtime_checkable

from overload_web.domain import model


@runtime_checkable
class RepositoryProtocol(Protocol):
    def get(self, id: Union[str, int]) -> model.Template: ...

    def save(self, template: model.Template) -> None: ...


class SqlAlchemyRepository:
    def __init__(self, session):
        self.session = session

    def get(self, id: Union[str, int]):
        return self.session.query(model.Template).filter_by(id=id).first()

    def save(self, template: model.Template) -> None:
        self.session.add(template)
