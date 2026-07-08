from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

from .customer import Customer
from .milk_entry import MilkEntry
from .payment import Payment
from .expense import Expense
from .cattle import Cattle
from .pregnancy import Pregnancy
from .setting import Setting
