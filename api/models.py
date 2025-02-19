from sqlmodel import Field, SQLModel

class Requests(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    dt: str = Field(default=None)
    action: str = Field(default=None)
    payload: str = Field(default=None)

    def create(self, session):
        session.add(self)
        session.commit()
        session.refresh(self)
        return self
    
class Logs(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    dt: str = Field(default=None)
    action: str = Field(default=None)
    payload: str = Field(default=None)
    internal_payload: str = Field(default=None)

    def create(self, session):
        session.add(self)
        session.commit()
        session.refresh(self)
        return self