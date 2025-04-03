class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///invoice.db'  # SQLite database file
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'
    JWT_SECRET_KEY = 'your_jwt_secret_key'
