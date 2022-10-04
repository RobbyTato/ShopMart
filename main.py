import tkinter as tk
from PIL import Image, ImageTk
from urllib.request import urlopen, Request
from urllib.error import URLError
import customtkinter as ctk
import io
import database
import sys
import random

try:
    _url = "https://www.google.com"
    urlopen(Request(_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}))
except URLError:
    print("This app requires an active internet connection. Please connect to the internet and run this file again.")
    sys.exit(-1)

cart = {}
login_details = []

win = ctk.CTk()
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
win.geometry("1280x900")
win.resizable(False, False)
win.title("ShopMart")

win.rowconfigure(0, minsize=75)
win.columnconfigure(0, weight=1)
win.rowconfigure(1, minsize=100, weight=1)

bottom = ctk.CTkFrame(win)
bottom.rowconfigure(0, weight=1)
bottom.columnconfigure(0, weight=4)
bottom.columnconfigure(1, minsize=100)

current_top_frame = None


def get_image_resize(url, dim=None):
    u = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}))
    data = u.read()
    u.close()
    image = Image.open(io.BytesIO(data))
    if dim:
        image = image.resize(dim, Image.ANTIALIAS)
    image = ImageTk.PhotoImage(image)
    return image


def get_image_thumbnail(url, dim=None):
    u = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}))
    data = u.read()
    u.close()
    image = Image.open(io.BytesIO(data))
    if dim:
        image.thumbnail(dim, Image.ANTIALIAS)
    image = ImageTk.PhotoImage(image)
    return image


def add_to_cart(_id):
    if cart.get(_id):
        cart[_id] += 1
    else:
        cart[_id] = 1
    cart_num = sum([cart[i] for i in cart])
    cart_text.set(cart_num)


def remove_from_cart(_id):
    cart[_id] -= 1
    if cart[_id] == 0:
        cart.pop(_id)
    cart_num = sum([cart[i] for i in cart])
    cart_text.set(cart_num)
    swap_frame("Cart")


def delete_order(_id):
    order_ids = eval(login_details[2])
    order_ids.remove(_id)
    login_details[2] = str(order_ids)
    database.execute("UPDATE Users SET orders = ? WHERE username = ?", (login_details[2], login_details[0]))
    database.execute("DELETE FROM Orders WHERE order_id = ?", (str(_id),))
    swap_frame("Account")


def confirm_login_details(username, password):
    global login_details
    user = database.fetchone("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
    if user:
        login_details = list(user)
        swap_frame("Account")
    else:
        swap_frame("Login Invalid")


def confirm_reg_details(username, password, confirm):
    global login_details
    user = database.fetchone("SELECT * FROM Users WHERE username = ?", (username,))
    if password != confirm:
        swap_frame("Register Password Error")
    elif user:
        swap_frame("Register Username Error")
    else:
        database.execute("INSERT INTO Users (username, password, orders) VALUES (?, ?, '[]')", (username, password))
        login_details = [username, password, '[]', None, None, None, None, None]
        swap_frame("Account")


def confirm_payment_details(cc, sec_code, expiry, visa_or_mc, address, save):
    if len(cc) != 16:
        swap_frame("Payment CC Error")
    elif len(sec_code) not in (3, 4):
        swap_frame("Payment Security Error")
    elif len(expiry) != 5 and 1 <= int(expiry[0:2]) <= 12:
        swap_frame("Payment Expiry Error")
    elif visa_or_mc not in ('visa', 'mc'):
        swap_frame("Payment VISA/MC Error")
    elif not address:
        swap_frame("Payment Address Error")
    else:
        order_id = random.randrange(1000, 10000)
        order_ids = eval(login_details[2])
        order_ids.append(order_id)
        login_details[2] = str(order_ids)
        if save == 1:
            login_details[3] = cc
            login_details[4] = sec_code
            login_details[5] = expiry
            login_details[6] = visa_or_mc
            login_details[7] = address
            database.execute(
                "UPDATE Users SET orders = ?, card_no = ?, expiry = ?, security_no = ?, visa_or_mc = ?, address = ? WHERE username = ?",
                tuple(login_details[2:]) + tuple(login_details[0]))
        else:
            database.execute("UPDATE Users SET orders = ? WHERE username = ?", (login_details[2], login_details[0]))
        items = str(cart)
        database.execute("INSERT INTO Orders VALUES (?, ?)", (str(order_id), items))
        swap_frame("Confirm payment")


def swap_frame(name):
    global current_top_frame, login_details, cart, cart_text
    if current_top_frame is not None:
        current_top_frame.destroy()
    if name in category_names or name == "Categories":
        left = ctk.CTkFrame(bottom)
        left.rowconfigure(0, weight=1)
        left.rowconfigure(1, weight=1, minsize=250)
        left.rowconfigure(2, weight=1, minsize=250)
        if name == "Categories":
            items = []
        else:
            query = f"SELECT * FROM Items WHERE category = '{name}'"
            items = database.fetchall(query)
        for i in range(3):
            left.columnconfigure(i, weight=1)
        for i in range(2):
            for j in range(3):
                thing = ctk.CTkFrame(left)
                if name == "Categories":
                    url = "https://cdn.discordapp.com/attachments/1024362106264494100/" + category_img[(3 * i) + j]
                    text = category_names[(3 * i) + j]
                    func = lambda i=i, j=j: swap_frame(category_names[(3 * i) + j])
                else:
                    url = "https://cdn.discordapp.com/attachments/1024362106264494100/" + items[(3 * i) + j][3]
                    text = items[(3 * i) + j][1]
                    func = lambda i=i, j=j: swap_frame(items[(3 * i) + j][1])
                img = get_image_resize(url, dim=(300, 300))
                img_label = ctk.CTkLabel(thing, image=img)
                img_label.image = img
                img_label.pack(fill=tk.X)
                button = ctk.CTkButton(thing, text=text, text_font=("Arial", 12), command=func)
                button.pack()
                thing.grid(row=i + 1, column=j, sticky="nswe", padx="30", pady="30")
        text = ctk.CTkLabel(left, text=name, text_font=("Arial", 30), anchor="center")
        text.grid(row=0, column=1, sticky="nswe")
        left.grid(row=0, column=0, sticky="nswe")
        current_top_frame = left
    elif name.startswith("Login"):
        if login_details:
            swap_frame("Account")
        else:
            left = ctk.CTkFrame(bottom)
            left.columnconfigure(0, weight=1)
            left.rowconfigure(0, weight=1)
            login = ctk.CTkFrame(left)
            form = ctk.CTkFrame(login)
            heading = ctk.CTkLabel(login, text="Login", text_font=("Arial", 40))
            username_text = ctk.CTkLabel(form, text="Username:", text_font=("Arial", 20))
            password_text = ctk.CTkLabel(form, text="Password:", text_font=("Arial", 20))
            username = ctk.CTkEntry(form)
            password = ctk.CTkEntry(form, show="*")
            login_btn = ctk.CTkButton(form, text="Login",
                                      command=lambda: confirm_login_details(username.get(), password.get()))
            register_btn = ctk.CTkButton(form, text="Register", command=lambda: swap_frame("Register"))
            heading.pack(padx=30, pady=30)
            username_text.grid(row=0, column=0, pady=15, sticky="W")
            username.grid(row=0, column=1, pady=15)
            password_text.grid(row=1, column=0, pady=15, sticky="W")
            password.grid(row=1, column=1, pady=15)
            if name == "Login Invalid":
                error = ctk.CTkLabel(form, text="Invalid username/password", text_color="red")
                error.grid(row=2, columnspan=2, pady=15)
            login_btn.grid(row=3, column=0, pady=15)
            register_btn.grid(row=3, column=1, pady=15)
            form.pack()
            login.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            left.grid(row=0, column=0, sticky="nswe")
            current_top_frame = left
    elif name.startswith("Register"):
        if login_details:
            swap_frame("Account")
        else:
            left = ctk.CTkFrame(bottom)
            left.columnconfigure(0, weight=1)
            left.rowconfigure(0, weight=1)
            login = ctk.CTkFrame(left)
            form = ctk.CTkFrame(login)
            heading = ctk.CTkLabel(login, text="Register", text_font=("Arial", 40))
            username_text = ctk.CTkLabel(form, text="Username:", text_font=("Arial", 20))
            password_text = ctk.CTkLabel(form, text="Password:", text_font=("Arial", 20))
            confirm_text = ctk.CTkLabel(form, text="Confirm password:", text_font=("Arial", 20))
            username = ctk.CTkEntry(form)
            password = ctk.CTkEntry(form, show="*")
            confirm = ctk.CTkEntry(form, show="*")
            register_btn = ctk.CTkButton(form, text="Register", command=lambda: confirm_reg_details(username.get(),
                                                                                                    password.get(),
                                                                                                    confirm.get()))
            heading.pack(padx=30, pady=30)
            username_text.grid(row=0, column=0, pady=15, sticky="W")
            username.grid(row=0, column=1, pady=15)
            password_text.grid(row=1, column=0, pady=15, sticky="W")
            password.grid(row=1, column=1, pady=15)
            confirm_text.grid(row=2, column=0, pady=15, sticky="W")
            confirm.grid(row=2, column=1, pady=15)
            if name == "Register Password Error":
                error = ctk.CTkLabel(form, text="Check if password is entered properly", text_color="red")
                error.grid(row=3, columnspan=2, pady=15)
            elif name == "Register Username Error":
                error = ctk.CTkLabel(form, text="Username already exists", text_color="red")
                error.grid(row=3, columnspan=2, pady=15)
            register_btn.grid(row=4, columnspan=2, pady=15)
            form.pack()
            login.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            left.grid(row=0, column=0, sticky="nswe")
            current_top_frame = left
    elif name == "Account":
        left = ctk.CTkFrame(bottom)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        acc = ctk.CTkFrame(left)
        welcome = ctk.CTkLabel(acc, text=f"Welcome, {login_details[0]}", text_font=("Arial", 40))
        welcome.pack(pady=30)
        if login_details[2] != '[]':
            l = eval(login_details[2])
            thing = ctk.CTkFrame(acc)
            for i, v in enumerate(l):
                order_no = ctk.CTkLabel(thing, text=f"Order #{v}", text_font=("Arial", 20))
                see_order_btn = ctk.CTkButton(thing, text="See order", text_font=("Arial", 20),
                                              command=lambda v=v: swap_frame(f"See order {v}"))
                delete_btn = ctk.CTkButton(thing, text="Delete", text_font=("Arial", 20),
                                           command=lambda v=v: delete_order(v))
                order_no.grid(row=i, column=0, padx=5, pady=5)
                see_order_btn.grid(row=i, column=1, padx=5, pady=5)
                delete_btn.grid(row=i, column=2, padx=5, pady=5)
            thing.pack()
        else:
            label = ctk.CTkLabel(acc, text="No orders yet", text_font=("Arial", 20))
            label.pack(padx=5, pady=5)
        acc.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        left.grid(row=0, column=0, sticky="nswe")
        current_top_frame = left
    elif name == "Cart":
        left = ctk.CTkFrame(bottom)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        cart_frame = ctk.CTkFrame(left)
        heading = ctk.CTkLabel(cart_frame, text=f"Cart", text_font=("Arial", 40))
        heading.pack(pady=30)
        if cart:
            thing = ctk.CTkFrame(cart_frame)
            total_price = 0
            for i, v in enumerate(cart):
                item = database.fetchone("SELECT * FROM Items WHERE id = ?", (v,))
                name = ctk.CTkLabel(thing, text=item[1], text_font=("Arial", 20))
                times = ctk.CTkLabel(thing, text="x" + str(cart[v]), text_font=("Arial", 20))
                price = ctk.CTkLabel(thing, text=str(item[2] * cart[v]), text_font=("Arial", 20))
                remove = ctk.CTkButton(thing, text="X", command=lambda v=v: remove_from_cart(v),
                                       text_font=("Arial", 20), width=20, height=20)
                total_price += item[2] * cart[v]
                name.grid(row=i, column=0, padx=5, pady=5)
                times.grid(row=i, column=1, padx=5, pady=5)
                price.grid(row=i, column=2, padx=5, pady=5)
                remove.grid(row=i, column=3, padx=5, pady=5)
            total_label = ctk.CTkLabel(thing, text="Total", text_font=("Arial", 20))
            total_label.grid(row=len(cart), column=0, padx=5, pady=5)
            total_price_label = ctk.CTkLabel(thing, text=str(total_price), text_font=("Arial", 20))
            total_price_label.grid(row=len(cart), column=2, padx=5, pady=5)
            purchase = ctk.CTkButton(thing, text="Purchase", command=lambda: swap_frame("Payment"))
            purchase.grid(row=len(cart) + 1, column=2, padx=5, pady=5)
            thing.pack()
        else:
            label = ctk.CTkLabel(cart_frame, text="Nothing is in your cart", text_font=("Arial", 20))
            label.pack(padx=5, pady=5)
        cart_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        left.grid(row=0, column=0, sticky="nswe")
        current_top_frame = left
    elif name.startswith("Payment"):
        if not login_details:
            swap_frame("Login")
        elif login_details[3:] != [None, None, None, None, None]:
            order_id = random.randrange(1000, 10000)
            order_ids = eval(login_details[2])
            order_ids.append(order_id)
            login_details[2] = str(order_ids)
            database.execute("UPDATE Users SET orders = ? WHERE username = ?", (login_details[2], login_details[0]))
            items = str(cart)
            database.execute("INSERT INTO Orders VALUES (?, ?)", (str(order_id), items))
            swap_frame("Confirm payment")
        else:
            left = ctk.CTkFrame(bottom)
            left.columnconfigure(0, weight=1)
            left.rowconfigure(0, weight=1)
            payment = ctk.CTkFrame(left)
            form = ctk.CTkFrame(payment)
            heading = ctk.CTkLabel(payment, text="Payment", text_font=("Arial", 40))
            cc_text = ctk.CTkLabel(form, text="Credit card number:", text_font=("Arial", 20))
            sec_code_text = ctk.CTkLabel(form, text="Security code (CVV):", text_font=("Arial", 20))
            address_text = ctk.CTkLabel(form, text="Address", text_font=("Arial", 20))
            expiry_text = ctk.CTkLabel(form, text="Expiry date (MM/YY)", text_font=("Arial", 20))
            cc = ctk.CTkEntry(form)
            sec_code = ctk.CTkEntry(form)
            address = ctk.CTkEntry(form)
            expiry = ctk.CTkEntry(form)
            visa_or_mc = tk.StringVar()
            visa_or_mc.set("visa")
            visa = ctk.CTkRadioButton(form, text="Visa", variable=visa_or_mc, value="visa")
            mc = ctk.CTkRadioButton(form, text="Mastercard", variable=visa_or_mc, value="mc")
            save_details = tk.IntVar()
            save_details.set(0)
            save = ctk.CTkRadioButton(form, text="Save details", variable=save_details, value=1)
            purchase = ctk.CTkButton(form, text="Purchase",
                                     command=lambda: confirm_payment_details(cc.get(),
                                                                             sec_code.get(),
                                                                             expiry.get(),
                                                                             visa_or_mc.get(),
                                                                             address.get(),
                                                                             save_details.get()))
            heading.pack(padx=30, pady=30)
            cc_text.grid(row=0, column=0, pady=15, sticky="W")
            cc.grid(row=0, column=1, pady=15, sticky="E")
            sec_code_text.grid(row=1, column=0, pady=15, sticky="W")
            sec_code.grid(row=1, column=1, pady=15, sticky="E")
            expiry_text.grid(row=2, column=0, pady=15, sticky="W")
            expiry.grid(row=2, column=1, pady=15, sticky="E")
            address_text.grid(row=3, column=0, pady=15, sticky="W")
            address.grid(row=3, column=1, pady=15, sticky="E")
            visa.grid(row=4, column=0, pady=15, sticky="E")
            mc.grid(row=4, column=1, pady=15, sticky="W")
            save.grid(row=5, columnspan=2, pady=15)
            if name == "Payment CC Error":
                error = ctk.CTkLabel(form, text="Credit card number must be 16 digits", text_color="red")
                error.grid(row=6, columnspan=2, pady=15)
            elif name == "Payment Security Error":
                error = ctk.CTkLabel(form, text="CVV must be 3 or 4 digits", text_color="red")
                error.grid(row=6, columnspan=2, pady=15)
            elif name == "Payment Expiry Error":
                error = ctk.CTkLabel(form, text="Expiry date is invalid", text_color="red")
                error.grid(row=6, columnspan=2, pady=15)
            elif name == "Payment VISA/MC Error":
                error = ctk.CTkLabel(form, text="Must pick either Visa or Mastercard", text_color="red")
                error.grid(row=6, columnspan=2, pady=15)
            elif name == "Payment VISA/MC Error":
                error = ctk.CTkLabel(form, text="Invalid Address", text_color="red")
                error.grid(row=6, columnspan=2, pady=15)
            purchase.grid(row=7, columnspan=2, pady=15)
            form.pack()
            payment.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            left.grid(row=0, column=0, sticky="nswe")
            current_top_frame = left
    elif name == "Confirm payment":
        cart = {}
        cart_text.set("0")
        left = ctk.CTkFrame(bottom)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        confirmed = ctk.CTkFrame(left)
        heading = ctk.CTkLabel(confirmed, text="Payment Confirmed", text_font=("Arial", 50))
        heading.pack()
        confirmed.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        left.grid(row=0, column=0, sticky="nswe")
        current_top_frame = left
        win.after(3000, lambda: swap_frame("Categories"))
    elif name.startswith("See order"):
        left = ctk.CTkFrame(bottom)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        order_frame = ctk.CTkFrame(left)
        heading = ctk.CTkLabel(order_frame, text=f"Order", text_font=("Arial", 40))
        heading.pack(pady=30)
        order = eval(database.fetchone("SELECT * FROM Orders WHERE order_id = ?", (name[10:],))[1])
        thing = ctk.CTkFrame(order_frame)
        total_price = 0
        for i, v in enumerate(order):
            item = database.fetchone("SELECT * FROM Items WHERE id = ?", (v,))
            name = ctk.CTkLabel(thing, text=item[1], text_font=("Arial", 20))
            times = ctk.CTkLabel(thing, text="x" + str(order[v]), text_font=("Arial", 20))
            price = ctk.CTkLabel(thing, text=str(item[2] * order[v]), text_font=("Arial", 20))
            total_price += item[2] * order[v]
            name.grid(row=i, column=0, padx=5, pady=5)
            times.grid(row=i, column=1, padx=5, pady=5)
            price.grid(row=i, column=2, padx=5, pady=5)
        total_label = ctk.CTkLabel(thing, text="Total", text_font=("Arial", 20))
        total_label.grid(row=len(order), column=0, padx=5, pady=5)
        total_price_label = ctk.CTkLabel(thing, text=str(total_price), text_font=("Arial", 20))
        total_price_label.grid(row=len(order), column=2, padx=5, pady=5)
        thing.pack()
        order_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        left.grid(row=0, column=0, sticky="nswe")
        current_top_frame = left
    else:
        left = ctk.CTkFrame(bottom)
        left.columnconfigure(0, weight=1, minsize=300)
        left.columnconfigure(1, weight=1, minsize=300)
        left.rowconfigure(0, weight=1)
        query = "SELECT * FROM Items WHERE name = ?"
        item = database.fetchone(query, (name,))
        url = "https://cdn.discordapp.com/attachments/1024362106264494100/" + item[3]
        img = get_image_thumbnail(url, dim=(400, 400))
        img_label = ctk.CTkLabel(left, image=img)
        img_label.image = img
        img_label.grid(row=0, column=0, sticky="nswe")
        item_frame = ctk.CTkFrame(left)
        rating_text = ((5 - int(item[6])) * "☆") + (int(item[6]) * "★")
        no_of_ratings_text = str(int(item[7])) + " ratings"
        supplier_text = "By " + item[4]
        price_text = str(int(item[2])) + " QR"
        name = ctk.CTkLabel(item_frame, text=item[1], text_font=("Arial", 30), anchor="e")
        rating = ctk.CTkLabel(item_frame, text=rating_text, text_color="yellow", anchor="e", text_font=("Arial", 15))
        no_of_ratings = ctk.CTkLabel(item_frame, text=no_of_ratings_text, text_color="gray", anchor="e",
                                     text_font=("Arial", 15))
        supplier = ctk.CTkLabel(item_frame, text=supplier_text, text_color="gray", anchor="e", text_font=("Arial", 15))
        price = ctk.CTkLabel(item_frame, text=price_text, text_font=("Arial", 23), anchor="e")
        cart_img = get_image_resize(
            "https://cdn.discordapp.com/attachments/1024362106264494100/1024743920225243197/cart.png", dim=(35, 35))
        cart_btn = ctk.CTkButton(item_frame, text="Add to cart", text_font=("Arial", 23), image=cart_img,
                                 command=lambda: add_to_cart(item[0]))
        name.pack(fill=tk.X, pady=20)
        rating.pack(fill=tk.X)
        no_of_ratings.pack(fill=tk.X)
        supplier.pack(fill=tk.X)
        price.pack(fill=tk.X, pady=20)
        cart_btn.pack(ipadx=5, ipady=5)
        item_frame.grid(row=0, column=1, sticky="e")
        left.grid(row=0, column=0, sticky="nswe")
        current_top_frame = left


category_img = ("1024377134673821836/electronics.jpg",
                "1024421709689913424/unknown.png",
                "1024377135445573733/furnitures.jpg",
                "1024377135693045781/grocery.png",
                "1024377134405398558/toys.jpg",
                "1024377134002753637/schoolaccessories.jpg")

category_names = ("Electronics",
                  "Workout Equipment",
                  "Furnitures",
                  "Groceries",
                  "Toys",
                  "School Accessories")

ads = ("1026581273088626798/unknown.png",
       "1026581303749005362/unknown.png",
       "1026581368446140426/unknown.png",
       "1026581461429653554/unknown.png",
       "1026581529645821962/unknown.png")


ad_img = get_image_resize("https://cdn.discordapp.com/attachments/1024362106264494100/" + random.choice(ads),
                          dim=(160, 600))
ad = ctk.CTkLabel(bottom, image=ad_img)
ad.grid(row=0, column=1, sticky="nswe")

swap_frame("Categories")

navbar = ctk.CTkFrame(win)
navbar.rowconfigure(0, weight=1)
navbar.columnconfigure(0, weight=1)
navbar.columnconfigure(1, weight=1)
navbar.columnconfigure(2, weight=1, minsize=300)

home = ctk.CTkButton(navbar, text="Home", height=40, width=60, text_font=("Arial", 18),
                     command=lambda: swap_frame("Categories"))
home.grid(row=0, column=0, sticky="w", padx="30")
cart_img = get_image_resize("https://cdn.discordapp.com/attachments/1024362106264494100/1024743920225243197/cart.png",
                            dim=(25, 25))
title = ctk.CTkLabel(navbar, text="ShopMart", text_font=("HGPSoeiKakupoptai", 30))
title.grid(row=0, column=1, sticky="nswe")
cart_text = tk.StringVar()
cart_text.set("0")
cart_btn = ctk.CTkButton(navbar, image=cart_img, width=40, height=40, textvariable=cart_text, text_font=("Arial", 15),
                         command=lambda: swap_frame("Cart"))
cart_btn.grid(row=0, column=2, sticky="e", padx="30")
acc_img = get_image_resize("https://cdn.discordapp.com/attachments/1024362106264494100/1024993769013116938/account.png",
                           dim=(25, 25))
acc_btn = ctk.CTkButton(navbar, text="", image=acc_img, width=40, height=40, command=lambda: swap_frame("Login"))
acc_btn.grid(row=0, column=2, sticky="e", padx="110")
navbar.grid(row=0, column=0, sticky="nswe")
bottom.grid(row=1, column=0, sticky="nswe")


win.mainloop()
