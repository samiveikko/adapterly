"""
Account model - mirrors Django accounts_account table.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class Account(Base):
    """Account model - mirrors accounts_account table."""

    __tablename__ = "accounts_account"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    external_id = Column(String(255), unique=True, nullable=True, index=True)
    default_project_id = Column(Integer, ForeignKey("mcp_project.id"), nullable=True)

    # Relationships
    mcp_api_keys = relationship("MCPApiKey", back_populates="account")
    agent_profiles = relationship("AgentProfile", back_populates="account")
    projects = relationship("Project", back_populates="account", foreign_keys="Project.account_id")
    default_project = relationship("Project", foreign_keys=[default_project_id])

    def __repr__(self):
        return f"<Account(id={self.id}, name='{self.name}')>"
