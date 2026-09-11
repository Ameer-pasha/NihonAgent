# schemas.py
from typing import List, Optional
from pydantic import BaseModel, Field

class CompanyResearchBrief(BaseModel):
    company_name: str = Field(default="Target Company", description="Target company name")
    open_roles: List[str] = Field(default_factory=list, description="List of open roles")
    tech_stack: List[str] = Field(default_factory=list, description="Technologies & skills")
    salary_band: Optional[str] = Field(default="Not specified", description="Salary range")
    visa_sponsorship: Optional[str] = Field(default="Unknown", description="Visa details")
    recent_news: Optional[str] = Field(default="None", description="Recent news")
    sources: List[str] = Field(default_factory=list, description="Sources URLs")