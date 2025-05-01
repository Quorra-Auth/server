from sqlmodel import Field, SQLModel

class OnboardingLink(SQLModel, table=True):
    link_id: str = Field(index=True, primary_key=True)

