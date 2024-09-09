from langchain_community.utilities import SQLDatabase


class Config:
    GEMINI_MODEL_NAME = "models/gemini-1.5-flash-001"
    DB_PATH = SQLDatabase.from_uri("sqlite:///os_data.db")
