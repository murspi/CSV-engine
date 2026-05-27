from pydantic import BaseModel

class ProcessResponse(BaseModel):
    success_or_failure: bool
    rows_in: int
    rows_out: int
    duplicates_dropped: int
    required_field_violations_dropped: int
    columns_validated: list[str]