import sqlite3
import random
import os


db_name = "database.db"

def check_db_exists():
    return os.path.exists("./" + db_name)


def init_db():
    init_items()
    init_users()
    init_orders()
    init_example()


def init_items():
    con = None
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        query = """CREATE TABLE IF NOT EXISTS Items(
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            img TEXT NOT NULL,
            manufacturer TEXT NOT NULL,
            category TEXT NOT NULL,
            rating INTEGER NOT NULL,
            no_of_ratings INTEGER NOT NULL)
            """
        cur.execute(query)
        cur.close()
        con.commit()
    except sqlite3.Error as e:
        print("An unexpected error with sqlite3 has occurred!")
        print(e)
        con.rollback()
    finally:
        if con:
            con.close()


def init_users():
    con = None
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        query = """CREATE TABLE IF NOT EXISTS Users(
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            orders TEXT NOT NULL,
            card_no TEXT,
            expiry TEXT,
            security_no TEXT,
            visa_or_mc TEXT,
            address TEXT)
            """
        cur.execute(query)
        cur.close()
        con.commit()
    except sqlite3.Error as e:
        print("An unexpected error with sqlite3 has occurred!")
        print(e)
        con.rollback()
    finally:
        if con:
            con.close()


def init_orders():
    con = None
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        query = """CREATE TABLE IF NOT EXISTS Orders(
            order_id TEXT NOT NULL,
            items TEXT NOT NULL)
            """
        cur.execute(query)
        cur.close()
        con.commit()
    except sqlite3.Error as e:
        print("An unexpected error with sqlite3 has occurred!")
        print(e)
        con.rollback()
    finally:
        if con:
            con.close()


def init_example():
    con = None
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        items = {"Electronics": ((1, "iPhone 13 Pro Max", 3999, "1024362133485539468/unknown.png", "Apple"),
                                 (2, "Samsung Z Fold 4", 6800, "1024362525850079272/unknown.png", "Samsung"),
                                 (3, "MacBook M1", 4599, "1024362761574174772/unknown.png", "Apple"),
                                 (4, "Galaxy Watch5", 1260, "1024363162868400210/unknown.png", "Samsung"),
                                 (5, "ROG Gaming laptop", 10950, "1024363677983440906/unknown.png", "ROG"),
                                 (6, "Keychron K2 Mechanical Keyboard", 300, "1024384154365861930/unknown.png", "Keychron")),
                 "School Accessories": ((7, "Ball Pens 5 pcs", 20, "1024385387965190265/unknown.png", "Win Guide"),
                                        (8, "Mechanical Pencil 3 pcs", 30, "1024385437952917544/unknown.png", "Pentel"),
                                        (9, "Metal Ruler 1 pc", 10, "1024385526410784798/unknown.png", "Kraf"),
                                        (10, "School Bag", 600, "1024385565757554708/unknown.png", "Adidas"),
                                        (11, "Correction Pen 1 pc", 10, "1024385752349560963/unknown.png", "Pentel"),
                                        (12, "Stapler", 60, "1024385951193112597/unknown.png", "Swingline")),
                 "Toys": ((13, "Dueling Lightsaber RGB", 310, "1024389624690376794/unknown.png", "YIXUN-US"),
                          (14, "Rubik's Cube 3x3", 36, "1024390112987054121/unknown.png", "Spin Master"),
                          (15, "Rubik's Cube 4x4", 72, "1024390512293191680/unknown.png", "Spin Master"),
                          (16, "Rainbow Fidget Spinner", 26, "1024390854774902804/unknown.png", "i-top"),
                          (17, "Stress Relief Ball", 44, "1024391189421621248/unknown.png", "Impresa"),
                          (18, "Slinky Spring Toy", 10, "1024391550899331152/unknown.png", "Amazon")),
                 "Groceries": ((19, "Spain Iceberg Lettuce 1 pc", 12, "1024395255505756371/unknown.png", "talabat"),
                               (20, "Red Onion Indian 1 kg", 4, "1024395586188869702/unknown.png", "talabat"),
                               (21, "Garlic China 500 g", 4, "1024407745350344765/unknown.png", "talabat"),
                               (22, "Potato Lebanon 1 kg", 4, "1024407940184146011/unknown.png", "Lulu hypermarket"),
                               (23, "Alphonso Mango 1 kg", 15, "1024408558445543544/unknown.png", "Lulu hypermarket"),
                               (24, "Apple Royal Gala France 1 kg", 7, "1024408796283539536/unknown.png", "Lulu hypermarket")),
                 "Workout Equipment": ((25, "Fitness Exercise Mat", 250, "1024421856217927710/unknown.png", "MICRODRY"),
                                       (26, "Ab Roller", 95, "1024422124854710282/unknown.png", "VINSGUIR"),
                                       (27, "Marcy Smith Cage Machine", 5475, "1024422561385283594/unknown.png", "Marcy"),
                                       (28, "Adjustable Dumbbell", 365, "1024423040873939054/unknown.png", "FLYBIRD"),
                                       (29, "Strength Training Bench", 620, "1024423239012847676/unknown.png", "FLYBIRD"),
                                       (30, "Hand Grip Strengthener", 150, "1024423607331463298/unknown.png", "Logest")),
                 "Furnitures": ((31, "Gaming Style Office Chair", 350, "1024415736569004103/unknown.png", "Amazon"),
                                (32, "Electric Adjustable Height Desk", 1825, "1024416571885621288/unknown.png", "DESIGNA"),
                                (33, "Benton Sofa Couch", 1095, "1024417160388411473/unknown.png", "ZINUS"),
                                (34, "Plant Pots 8 inch 2 pcs", 56, "1024417545496821790/unknown.png", "QCQHDU"),
                                (35, "Mini Fridge 1.7 Cubic Ft.", 480, "1024418401252294666/unknown.png", "BLACK+DECKER"),
                                (36, "Queen Sized Bed", 910, "1024419066733142066/unknown.png", "ZINUS"))}
        for i in items:
            for j in items[i]:
                query = "INSERT INTO Items VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                cur.execute(query, (*j, i, random.choices((3, 4, 5), (0.2, 0.2, 0.6), k=1)[0], random.randrange(30000, 100000)))
        cur.close()
        con.commit()
    except sqlite3.Error as e:
        print("An unexpected error with sqlite3 has occurred!")
        print(e)
        con.rollback()
    finally:
        if con:
            con.close()


def fetchall(query, param=None):
    if not check_db_exists():
        init_db()
    con = None
    result = []
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        if param:
            cur.execute(query, param)
        else:
            cur.execute(query)
        result = cur.fetchall()
        cur.close()
    except sqlite3.Error as e:
        print("An unexpected error with sqlite3 has occurred!")
        print(e)
        con.rollback()
    finally:
        if con:
            con.close()
        return result


def fetchone(query, param=None):
    if not check_db_exists():
        init_db()
    con = None
    result = []
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        if param:
            cur.execute(query, param)
        else:
            cur.execute(query)
        result = cur.fetchone()
        cur.close()
    except sqlite3.Error as e:
        print("An unexpected error with sqlite3 has occurred!")
        print(e)
        con.rollback()
    finally:
        if con:
            con.close()
        return result


def execute(query, param=None):
    if not check_db_exists():
        init_db()
    con = None
    try:
        con = sqlite3.connect(db_name)
        cur = con.cursor()
        if param:
            cur.execute(query, param)
        else:
            cur.execute(query)
        cur.close()
        con.commit()
    except sqlite3.Error as e:
        print("An unexpected error with sqlite3 has occurred!")
        print(e)
        con.rollback()
    finally:
        if con:
            con.close()


if __name__ == "__main__":
    if not check_db_exists():
        init_db()