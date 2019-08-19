# PWP SUMMER 2019
# Training Manager
# Group information
* Seppo Torniainen seppo.torniainen@gmail.com

Installing app / creating database (windows 10):

1) install Python 3.7.3+ and IPython
2) create virtual environment: python -m venv /path/to/the/virtualenv
3) activate virtual environment: c:\path\to\the\virtualenv\Scripts\activate.bat
4) install flask+sqllite+sqlalchemy: pip install Flask pysqlite3 flask-sqlalchemy
5) change to src directory: cd src
6) start ipython: ipython
7) In [1]: from app import db
8) In [2]: db.create_all()




