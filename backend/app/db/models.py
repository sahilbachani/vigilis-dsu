from sqlalchemy import Column, Integer, String, Boolean, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Source(Base):
    __tablename__ = "sources"
    source_id = Column(Integer, primary_key=True)
    platform = Column(String)
    source_name = Column(String)
    url = Column(String)
    added_date = Column(DateTime, default=datetime.utcnow)

class Post(Base):
    __tablename__ = "posts"
    post_id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.source_id"))
    author = Column(String)
    timestamp = Column(DateTime)
    text_content = Column(Text)
    url = Column(String)
    confidence_score = Column(Float)
    flagged = Column(Boolean, default=False)
    category = Column(String)

    media = relationship("PostMedia", back_populates="post", cascade="all, delete-orphan")

class PostMedia(Base):
    __tablename__ = "post_media"
    media_id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey("posts.post_id", ondelete="CASCADE"))
    media_type = Column(String)
    media_url = Column(String)
    local_path = Column(String)
    added_date = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="media")

class Video(Base):
    __tablename__ = "videos"
    video_id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.source_id"))
    url = Column(String)
    transcript = Column(Text)
    duration = Column(Float)
    ai_text_analysis_score = Column(Float)
    audio_emotion_score = Column(Float)
    visual_emotion_score = Column(Float)
    flagged = Column(Boolean, default=False)

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password_hash = Column(String)
    role = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class TagKeyword(Base):
    __tablename__ = "tags_keywords"

    tag_id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.post_id"), nullable=True)
    video_id = Column(Integer, ForeignKey("videos.video_id"), nullable=True)
    tag = Column(String, index=True)
    source_id = Column(Integer, ForeignKey("sources.source_id"))
    added_date = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TagKeyword(tag={self.tag}, post_id={self.post_id}, video_id={self.video_id})>"



