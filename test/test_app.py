import os
import pytest
import tempfile
import time
import sys
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")

from datetime import datetime
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError

import app
from app import User,TrainingCourse,CourseMedia

