from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True, index=True) # UUID string
    jd = Column(Text, nullable=False)
    resume_text = Column(Text, nullable=False)
    num_questions = Column(Integer, default=8)
    
    questions = relationship("Question", back_populates="session")

class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    question_text = Column(Text, nullable=False)
    category = Column(String)
    difficulty = Column(String)
    transcript = Column(Text)
    
    session = relationship("Session", back_populates="questions")
    scores = relationship("Score", back_populates="question", cascade="all, delete-orphan")

class Score(Base):
    __tablename__ = "scores"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"))
    dimension = Column(String, nullable=False)
    score_value = Column(Integer, nullable=False)
    justification = Column(Text)
    
    question = relationship("Question", back_populates="scores")
