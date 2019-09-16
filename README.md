# PWP SUMMER 2019
# Training Manager
# Group information
* Seppo Torniainen seppo.torniainen@gmail.com

Installing / running app (tested on windows 10):

1) install Python 3.7.3+ and IPython
2) create virtual environment: python -m venv /path/to/the/virtualenv
3) activate virtual environment: c:\path\to\the\virtualenv\Scripts\activate.bat
4) install flask+sqllite+sqlalchemy: pip install Flask pysqlite3 flask-sqlalchemy
5) copy this reposity from github to local machine
6) change to src directory: cd src
7) run app with flask : flask run
8) app creates database /db/database.db
9) app client can be accessed from http://localhost:5000/trainingmanager/client/

Testing : 

1) pip install pytest pytest-cov
2) change to test directory: cd test
3) run database and api tests: runtests.bat (or just pytest)


External libraries used : JQuery and Bootstrap (both in src\static folder)

Free images used from pixabay.com
