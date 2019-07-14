from time import time
from urllib.request import urlopen
from json import loads
import datetime

from .exceptions import *

class Meal:
    """Meal serving time"""
    BREAKFAST, LUNCH, SNACK, DINNER = range(4)

class Day:
    """Sage days"""
    SUNDAY, MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY = range(7)

class MenuCategory:
    """Sections of Sage menu"""
    STOCK_EXCHANGE, IMPROVISATIONS, CLASSIC_CUTS, MAIN_INGREDIENT, SEASONINGS, CROSSROADS, MANGIA_MANGIA, TRANSIT_FARE, PS, SPLASHES, VARIABLE, PAQUITOS, PACHIFIC_THYME, VEGITAS = range(14)

class HealthDot:
    """Sage nutrition dot rating"""
    RED, YELLOW, GREEN = range(1, 4)
    ALL = 6
    NIL = 0

    def get_dot_rating(i):
        """
        get a health dot given a numerical rating from Sage json
            :param i: sage rating as stored in json (1, 2, 3 == red, yellow, green)
        """
        if i == 1:
            return HealthDot.RED
        elif i == 2:
            return HealthDot.YELLOW
        elif i == 3:
            return HealthDot.GREEN
        elif i == 6:
            return HealthDot.ALL
        else:
            return HealthDot.NIL
        
    def get_readable_rating(i):
        """
        get a string representing the health rating of a given healthdot
            :param i: the rating of a dot
        """
        mapping = {
            1 : "red",
            2 : "yellow",
            3 : "green",
            6 : "all"
        }
        return mapping[i] if i in mapping else "nil"

def construct_query_url(school_id, cardinality=0):
    """
    Generate a URL to access a Sage menu
        :param school_id: id of menu/school to get data from
        :param cardinality=0: 
    """
    return "https://www.sagedining.com/intranet/apps/mb/pubasynchhandler.php?unitId={}&mbMenuCardinality={}&_={}".format(school_id, cardinality, int(time()))

class SageMenuItem:
    def __init__(self, sage_data):
        """
            :param sage_data: data for the menu item structured in the sage format
        """
        self.name = sage_data["t"]
        self.health_rating = HealthDot.get_dot_rating(sage_data["d"])

    def __str__(self):
        return self.name

class Sage:
    """Object to interface with Sage menu"""
    
    def __init__(self, school_id):
        """
            :param school_id: id of school menu to access
        """
        self.school_id = school_id
        self.menu_data = None
        self.menu_name = None
        self.meals_served = None
        self.first_date = None

    def update(self):
        """update the cached data"""
        with urlopen(construct_query_url(self.school_id)) as request:
            request_data = loads(request.read().decode("utf-8"))
        if "menu" not in request_data:
            raise NoMenusFound
        self.menu_name = request_data["unit"]["name"]
        self.first_date = datetime.datetime.fromtimestamp(int(request_data["menuList"][0]["menuFirstDate"]))
        raw_menu_data = request_data["menu"]
        self.meals_served = raw_menu_data["config"]["grid"]["mealsServed"]
        self.menu_data = raw_menu_data["menu"]["items"]
    
    def get_menu_date(self, date : datetime.datetime, meal):
        """
        get the menu for a given date and meal
            :param date: the date to get the menu for
            :param meal: the meal to get data for
        """
        self._ensure_updated()
        if meal not in range(0, 4):
            raise MealNotValid
        day_of_week = (date.weekday()+1)%7
        days_from_first = (date-self.first_date).days+1
        if days_from_first < 0:
            raise DateNotValid
        week = days_from_first // 7
        if week >= len(self.menu_data):
            raise DateNotValid
        return self.menu_data[week][day_of_week][meal]

    def get_categories_date(self, date : datetime.datetime, meal, categories):
        """
        get data for categories passed in
            :param date: the date to get the menu for
            :param meal: the meal to get data for
            :param categories: a list of categories to get data for
        """
        self._ensure_updated()
        menu = self.get_menu_date(date, meal)
        r = []
        for i in categories:
            if i >= len(menu):
                raise CategoryNotValid
            r.append([SageMenuItem(j) for j in menu[i]])
        return r

    def _ensure_updated(self):
        """make sure that the cache exists/is up to date"""
        if self.menu_data == None:
            raise MenuCacheNotPresent