from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clerk_id = Column(String, unique=True)
    email = Column(String)

class Project(Base):
    __tablename__ = "projects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True)
    name = Column(String)

class File(Base):
    __tablename__ = "files"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))
    name = Column(String)
    graph_json = Column(JSONB)
    is_deployed = Column(Boolean, default=False, server_default="false")
    deployed_path = Column(String, nullable=True)
    deployed_method = Column(String, nullable=True)

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, unique=True, index=True, nullable=False)
    label = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DatabaseConnection(Base):
    __tablename__ = "database_connections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    db_type = Column(String, nullable=False)
    encrypted_credentials = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class WorkflowExecutionLog(Base):
    __tablename__ = "workflow_execution_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("files.id"), index=True)
    execution_id = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True)
    status = Column(String)
    trace = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
