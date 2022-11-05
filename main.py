import tkinter as tk
from PIL import Image, ImageTk
from urllib.request import urlopen, Request
from urllib.error import URLError
import customtkinter as ctk
import io
import database
import sys
import random

# check for internet connection
try:
    # if error when accessing google, assume that internet is not available
    _url = "https://www.google.com"
    urlopen(Request(_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}))
except URLError:
    # error message
    print("This app requires an active internet connection. Please connect to the internet and run this file again.")
    sys.exit(-1)

# cart and user login details
cart = {}  # {"item name": quantity}
login_details = []  # [username, password, previous_order_ids, card_no, expiry, security_no, visa_or_mastercard, address]

# create and set window options
win = ctk.CTk()
ctk.set_appearance_mode("Dark")  # dark theme
ctk.set_default_color_theme("blue")  # blue color theme
win.geometry("1280x900")  # window size
win.resizable(False, False)  # resizing set to false
win.title("ShopMart")  # window name

win.rowconfigure(0, minsize=75)  # set navbar frame height
win.columnconfigure(0, weight=1)  # set width of all frames
win.rowconfigure(1, minsize=100, weight=1)  # set bottom frame height

bottom = ctk.CTkFrame(win)  # create frame that is below the navbar
bottom.rowconfigure(0, weight=1)  # set bottom frame height size
bottom.columnconfigure(0, weight=4)  # set main frame width size
bottom.columnconfigure(1, minsize=100)  # set ad frame width size

current_top_frame = None  # used to switch frames (to know which frame is being displayed)


def get_image_resize(url, dim=None):
    """
    Returns an image grabbed from the url. If dim is given, it will be resized to that size (original aspect ratio WILL
    NOT be maintained when resizing)
    :param url: The url containing the image
    :param dim: The pixel dimensions of final image
    :return: ImageTk.PhotoImage object (used to display images in app)
    """
    u = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}))  # open connection
    data = u.read()  # read data
    u.close()  # close connection
    image = Image.open(io.BytesIO(data))  # create image from data
    if dim:
        image = image.resize(dim, Image.ANTIALIAS)  # resize if dimensions given
    image = ImageTk.PhotoImage(image)  # convert to PhotoImage
    return image


def get_image_thumbnail(url, dim=None):
    """
    Returns an image grabbed from the url. If dim is given, it will be resized to that size (original aspect ratio WILL
    be maintained when resizing)
    :param url: The url containing the image
    :param dim: The pixel dimensions of final image
    :return: ImageTk.PhotoImage object (used to display images in app)
    """
    u = urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'}))  # open connection
    data = u.read()  # read data
    u.close()  # close connection
    image = Image.open(io.BytesIO(data))  # create image from data
    if dim:
        image.thumbnail(dim, Image.ANTIALIAS)  # resize if dimensions given (aspect ratio is maintained while resizing)
    image = ImageTk.PhotoImage(image)  # convert to PhotoImage
    return image


def add_to_cart(_id):
    """
    Put item into the cart using the item_id
    :param _id: id of the item
    """
    if cart.get(_id):
        cart[_id] += 1  # increase no by 1
    else:
        cart[_id] = 1  # add item to cart if not already present
    cart_num = sum([cart[i] for i in cart])  # get number of items
    cart_text.set(cart_num)  # change cart text to number of items


def remove_from_cart(_id):
    """
    Remove item from the cart using the item_id
    :param _id: id of the item
    """
    cart[_id] -= 1  # decrease no by 1
    if cart[_id] == 0:
        cart.pop(_id)  # if no of items = 0, remove from cart
    cart_num = sum([cart[i] for i in cart])  # get number of items
    cart_text.set(cart_num)  # change cart text to number of items
    swap_frame("Cart")  # refresh cart page to show updated number


def delete_order(_id):
    """
    Delete a completed order from the user account using the order_id
    :param _id: id of the completed order
    """
    order_ids = eval(login_details[2])  # get list of orders
    order_ids.remove(_id)  # remove order from list of orders
    login_details[2] = str(order_ids)  # update user's orders list
    database.execute("UPDATE Users SET orders = ? WHERE username = ?",
                     (login_details[2], login_details[0]))  # change in database
    database.execute("DELETE FROM Orders WHERE order_id = ?", (str(_id),))  # change in database
    swap_frame("Account")  # refresh account page to show updated orders


def confirm_login_details(username, password):
    """
    Check for any errors in the given login details. If error is present, it will change frame to give error, else
    update user details.
    :param username: Username of the user
    :param password: Password of the user
    """
    global login_details
    user = database.fetchone("SELECT * FROM Users WHERE username = ? AND password = ?", (username, password))
    if user:  # check if user is in the database
        login_details = list(user)  # change login details
        swap_frame("Account")  # change frame to account page
    else:
        swap_frame("Login Invalid")  # change frame to login error page


def confirm_reg_details(username, password, confirm):
    """
    Check for any errors in the given register details. If error is present, it will change frame to give error, else
    create user in database and update user details.
    :param username: Username
    :param password: Password
    :param confirm: Confirm password
    """
    global login_details
    user = database.fetchone("SELECT * FROM Users WHERE username = ?", (username,))
    if password != confirm:  # check if confirm password text = password text
        swap_frame("Register Password Error")  # change frame to registration error page
    elif user:  # check if user already exists in database
        swap_frame("Register Username Error")  # change frame to registration error page
    else:
        database.execute("INSERT INTO Users (username, password, orders) VALUES (?, ?, '[]')",
                         (username, password))  # create new user in database
        login_details = [username, password, '[]', None, None, None, None,
                         None]  # change login details (5 None's are for payment details, check line 23)
        swap_frame("Account")  # change frame to account page


def confirm_payment_details(cc, sec_code, expiry, visa_or_mc, address, save):
    """
    Check for any errors in the given payment details. If error is present, it will change frame to give error
    :param cc: Credit card no
    :param sec_code: Security code / CVV
    :param expiry: Expiry month and year
    :param visa_or_mc: Visa or Mastercard
    :param address: Billing address
    :param save: Do you want to save your payment details (True/False)
    """
    if len(cc) != 16:  # check if cc no is 16 digits long
        swap_frame("Payment CC Error")
    elif len(sec_code) not in (3, 4):  # check if security code is 3 or 4 digits long
        swap_frame("Payment Security Error")
    elif len(expiry) != 5 and 1 <= int(expiry[0:2]) <= 12:  # check if expiry date is valid
        swap_frame("Payment Expiry Error")
    elif visa_or_mc not in ('visa', 'mc'):  # check if "visa" or "mc" is given
        swap_frame("Payment VISA/MC Error")
    elif not address:  # check if billing address is given
        swap_frame("Payment Address Error")
    else:
        order_id = random.randrange(1000, 10000)  # create random order_id
        order_ids = eval(login_details[2])  # get list of orders
        order_ids.append(order_id)  # add order to list of orders
        login_details[2] = str(order_ids)  # update user's orders list
        if save == 1:  # ask if user wants to save payment details
            login_details[3] = cc
            login_details[4] = sec_code
            login_details[5] = expiry
            login_details[6] = visa_or_mc
            login_details[7] = address
            database.execute(
                "UPDATE Users SET orders = ?, card_no = ?, expiry = ?, security_no = ?, visa_or_mc = ?, address = ? WHERE username = ?",
                tuple(login_details[2:]) + tuple(login_details[0]))  # save payment details and order details
        else:
            database.execute("UPDATE Users SET orders = ? WHERE username = ?",
                             (login_details[2], login_details[0]))  # save only order details
        items = str(cart)
        database.execute("INSERT INTO Orders VALUES (?, ?)", (str(order_id), items))  # save items in order
        swap_frame("Confirm payment")  # change frame to confirm payment page


def swap_frame(name):
    """
    Main part of the program. When swap_frame("frame_name") is called, the app will switch to the given frame according
    to the name given. The following names are accepted:

    Categories: Shows the item categories
    <category_name>: Shows the items in specified category_name
    Login: Shows the login page
    Login <error>: Shows the login page with given error
    Register: Shows the registration page
    Register <error>: Shows the registration page with given error
    Account: Shows the logged in user's account page
    Cart: Shows the items in the user's cart
    Payment: Shows the page to pay for an order
    Payment <error>: Shows the page to pay for an order with given error
    Confirm payment: If payment finishes without any errors, a page with "Payment confirmed" is displayed
    See order <order_id>: Shows the completed order of a user using the order_id given
    <item_name>: Shows the page containing details for the item

    :param name: page name
    """
    global current_top_frame, login_details, cart, cart_text
    if current_top_frame is not None:
        current_top_frame.destroy()  # when function is called, the currently displayed page is deleted in order to switch it
    if name in category_names or name == "Categories":
        left = ctk.CTkFrame(bottom)  # create top frame
        left.rowconfigure(0, weight=1)  # set size for category title
        left.rowconfigure(1, weight=1, minsize=250)  # set size for first row of items
        left.rowconfigure(2, weight=1, minsize=250)  # set size for second row of items
        if name == "Categories":  # if main category page is requested, items are not required and set to []
            items = []
        else:  # if category name is given, the items in the category are taken from database
            query = f"SELECT * FROM Items WHERE category = '{name}'"
            items = database.fetchall(query)  # get items in category
        for i in range(3):
            left.columnconfigure(i, weight=1)  # set width of each grid item
        for i in range(2):
            for j in range(3):

                # grabs item details and displays it

                thing = ctk.CTkFrame(left)
                if name == "Categories":  # if main category page is requested, only category images are taken
                    url = "https://cdn.discordapp.com/attachments/1024362106264494100/" + category_img[(3 * i) + j]
                    text = category_names[(3 * i) + j]
                    func = lambda i=i, j=j: swap_frame(category_names[(3 * i) + j])
                else:  # if category name is given, the images of items are taken
                    url = "https://cdn.discordapp.com/attachments/1024362106264494100/" + items[(3 * i) + j][3]
                    text = items[(3 * i) + j][1]
                    func = lambda i=i, j=j: swap_frame(items[(3 * i) + j][1])
                img = get_image_resize(url, dim=(300, 300))  # resize image
                img_label = ctk.CTkLabel(thing, image=img)  # create image label
                img_label.image = img  # set label's image to item image
                img_label.pack(fill=tk.X)  # place item image
                button = ctk.CTkButton(thing, text=text, text_font=("Arial", 12), command=func)  # create item button
                button.pack()  # place item button
                thing.grid(row=i + 1, column=j, sticky="nswe", padx="30", pady="30")  # place item in the grid
        text = ctk.CTkLabel(left, text=name, text_font=("Arial", 30), anchor="center")  # create category name text
        text.grid(row=0, column=1, sticky="nswe")  # place category name text
        left.grid(row=0, column=0, sticky="nswe")  # place top frame
        current_top_frame = left  # set top frame
    elif name.startswith("Login"):
        if login_details:  # if already logged in, switch directly to account page
            swap_frame("Account")
        else:  # if not logged in, display login page
            left = ctk.CTkFrame(bottom)  # create top frame
            left.columnconfigure(0, weight=1)  # set width
            left.rowconfigure(0, weight=1)  # set height
            login = ctk.CTkFrame(left)  # create login frame
            form = ctk.CTkFrame(login)  # create form frame
            heading = ctk.CTkLabel(login, text="Login", text_font=("Arial", 40))  # create heading text
            username_text = ctk.CTkLabel(form, text="Username:", text_font=("Arial", 20))  # create username text
            password_text = ctk.CTkLabel(form, text="Password:", text_font=("Arial", 20))  # create password text
            username = ctk.CTkEntry(form)  # create username text box
            password = ctk.CTkEntry(form, show="*")  # create password text box
            login_btn = ctk.CTkButton(form, text="Login",
                                      command=lambda: confirm_login_details(username.get(),
                                                                            password.get()))  # create login button
            register_btn = ctk.CTkButton(form, text="Register", command=lambda: swap_frame("Register"))  # create register button (sends user to registration page_
            heading.pack(padx=30, pady=30)  # place heading text
            username_text.grid(row=0, column=0, pady=15, sticky="W")  # place login text
            username.grid(row=0, column=1, pady=15)  # place login text box
            password_text.grid(row=1, column=0, pady=15, sticky="W")  # place password text
            password.grid(row=1, column=1, pady=15)  # place password text box
            if name == "Login Invalid":  # error message
                error = ctk.CTkLabel(form, text="Invalid username/password", text_color="red")
                error.grid(row=2, columnspan=2, pady=15)
            login_btn.grid(row=3, column=0, pady=15)  # place login button
            register_btn.grid(row=3, column=1, pady=15)  # place register button
            form.pack()  # place form frame
            login.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # place login frame
            left.grid(row=0, column=0, sticky="nswe")  # place top frame
            current_top_frame = left  # set top frame
    elif name.startswith("Register"):
        if login_details:  # if already logged in, switch directly to account page
            swap_frame("Account")
        else:  # if not logged in, display registration page
            left = ctk.CTkFrame(bottom)  # create top frame
            left.columnconfigure(0, weight=1)  # set width
            left.rowconfigure(0, weight=1)  # set height
            login = ctk.CTkFrame(left)  # create registration frame
            form = ctk.CTkFrame(login)  # create form frame
            heading = ctk.CTkLabel(login, text="Register", text_font=("Arial", 40))  # create heading text
            username_text = ctk.CTkLabel(form, text="Username:", text_font=("Arial", 20))  # create username text
            password_text = ctk.CTkLabel(form, text="Password:", text_font=("Arial", 20))  # create password text
            confirm_text = ctk.CTkLabel(form, text="Confirm password:", text_font=("Arial", 20))  # create confirm password text
            username = ctk.CTkEntry(form)  # create username text box
            password = ctk.CTkEntry(form, show="*")  # create password text box
            confirm = ctk.CTkEntry(form, show="*")  # create confirm password text box
            register_btn = ctk.CTkButton(form, text="Register", command=lambda: confirm_reg_details(username.get(),
                                                                                                    password.get(),
                                                                                                    confirm.get())) # create register button
            heading.pack(padx=30, pady=30)  # place heading text
            username_text.grid(row=0, column=0, pady=15, sticky="W")  # place username text
            username.grid(row=0, column=1, pady=15)  # place username text box
            password_text.grid(row=1, column=0, pady=15, sticky="W")  # place password text
            password.grid(row=1, column=1, pady=15)  # place password text box
            confirm_text.grid(row=2, column=0, pady=15, sticky="W")  # place confirm password text
            confirm.grid(row=2, column=1, pady=15)  # place confirm password text box
            if name == "Register Password Error":  # error message
                error = ctk.CTkLabel(form, text="Check if password is entered properly", text_color="red")
                error.grid(row=3, columnspan=2, pady=15)
            elif name == "Register Username Error":  # error message
                error = ctk.CTkLabel(form, text="Username already exists", text_color="red")
                error.grid(row=3, columnspan=2, pady=15)
            register_btn.grid(row=4, columnspan=2, pady=15)  # place register button
            form.pack()  # place form frame
            login.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # place login frame
            left.grid(row=0, column=0, sticky="nswe")  # place top frame
            current_top_frame = left  # set top frame
    elif name == "Account":
        left = ctk.CTkFrame(bottom)  # create top frame
        left.columnconfigure(0, weight=1)  # set width
        left.rowconfigure(0, weight=1)  # set height
        acc = ctk.CTkFrame(left)  # create account frame
        welcome = ctk.CTkLabel(acc, text=f"Welcome, {login_details[0]}", text_font=("Arial", 40))  # create welcome text
        welcome.pack(pady=30)  # place welcome text
        if login_details[2] != '[]':  # if the user has any previous order, display them here
            l = eval(login_details[2])  # get list of orders
            thing = ctk.CTkFrame(acc)  # create orders frame
            for i, v in enumerate(l):  # grab index and value of order
                order_no = ctk.CTkLabel(thing, text=f"Order #{v}", text_font=("Arial", 20))  # get order number
                see_order_btn = ctk.CTkButton(thing, text="See order", text_font=("Arial", 20),
                                              command=lambda v=v: swap_frame(f"See order {v}"))  # create button to see details of that order
                delete_btn = ctk.CTkButton(thing, text="Delete", text_font=("Arial", 20),
                                           command=lambda v=v: delete_order(v))  # create button to delete order
                order_no.grid(row=i, column=0, padx=5, pady=5)  # place order no text
                see_order_btn.grid(row=i, column=1, padx=5, pady=5)  # place see order button
                delete_btn.grid(row=i, column=2, padx=5, pady=5)  # place delete order button
            thing.pack()  # place order in the grid
        else:  # if user has no orders, display text that says "No orders yet"
            label = ctk.CTkLabel(acc, text="No orders yet", text_font=("Arial", 20))
            label.pack(padx=5, pady=5)
        acc.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # place account frame
        left.grid(row=0, column=0, sticky="nswe")  # place top frame
        current_top_frame = left  # set top frame
    elif name == "Cart":
        left = ctk.CTkFrame(bottom)  # create top frame
        left.columnconfigure(0, weight=1)  # set width
        left.rowconfigure(0, weight=1)  # set height
        cart_frame = ctk.CTkFrame(left)  # create cart frame
        heading = ctk.CTkLabel(cart_frame, text=f"Cart", text_font=("Arial", 40))  # create heading text
        heading.pack(pady=30)  # place heading text
        if cart:  # if there are items in the cart, display the cart
            thing = ctk.CTkFrame(cart_frame)  # create item in cart frame
            total_price = 0  # used to calculate total price
            for i, v in enumerate(cart):  # grab index and value of item in cart
                item = database.fetchone("SELECT * FROM Items WHERE id = ?", (v,))  # get item from database
                name = ctk.CTkLabel(thing, text=item[1], text_font=("Arial", 20))  # create item name text
                times = ctk.CTkLabel(thing, text="x" + str(cart[v]), text_font=("Arial", 20))  # create no of items text
                price = ctk.CTkLabel(thing, text=str(item[2] * cart[v]), text_font=("Arial", 20))  # create item price text
                remove = ctk.CTkButton(thing, text="X", command=lambda v=v: remove_from_cart(v),
                                       text_font=("Arial", 20), width=20, height=20)  # create remove item button
                total_price += item[2] * cart[v]  # multiple no of items with price and add to total price
                name.grid(row=i, column=0, padx=5, pady=5)  # place item name text
                times.grid(row=i, column=1, padx=5, pady=5)  # place no of items text
                price.grid(row=i, column=2, padx=5, pady=5)  # place item price text
                remove.grid(row=i, column=3, padx=5, pady=5)  # place remove item text
            total_label = ctk.CTkLabel(thing, text="Total", text_font=("Arial", 20))  # create total price text
            total_label.grid(row=len(cart), column=0, padx=5, pady=5)  # place total price text
            total_price_label = ctk.CTkLabel(thing, text=str(total_price), text_font=("Arial", 20))  # create total price number text
            total_price_label.grid(row=len(cart), column=2, padx=5, pady=5)  # place total price number text
            purchase = ctk.CTkButton(thing, text="Purchase", command=lambda: swap_frame("Payment"))  # create purchase button
            purchase.grid(row=len(cart) + 1, column=2, padx=5, pady=5)  # place purchase button text
            thing.pack()  # place item in grid
        else:  # if no items in cart, display text that says "Nothing is in your cart"
            label = ctk.CTkLabel(cart_frame, text="Nothing is in your cart", text_font=("Arial", 20))
            label.pack(padx=5, pady=5)
        cart_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # place cart frame
        left.grid(row=0, column=0, sticky="nswe")  # place top frame
        current_top_frame = left  # set top frame
    elif name.startswith("Payment"):
        if not login_details:  # if not logged in, send user to login page
            swap_frame("Login")
        elif login_details[3:] != [None, None, None, None, None]:  # if payment details are saved, skip payment window and put order in database
            order_id = random.randrange(1000, 10000)  # create random order id
            order_ids = eval(login_details[2])  # get user's order list
            order_ids.append(order_id)  # add new order to order list
            login_details[2] = str(order_ids)  # update user's order list
            database.execute("UPDATE Users SET orders = ? WHERE username = ?", (login_details[2], login_details[0]))  # update user's order list in database
            items = str(cart)  # get items from cart
            database.execute("INSERT INTO Orders VALUES (?, ?)", (str(order_id), items))  # create new order in database
            swap_frame("Confirm payment")  # send user to payment confirmed page
        else:
            left = ctk.CTkFrame(bottom)  # create top frame
            left.columnconfigure(0, weight=1)  # set width
            left.rowconfigure(0, weight=1)  # set height
            payment = ctk.CTkFrame(left)  # create payment frame
            form = ctk.CTkFrame(payment)  # create form frame
            heading = ctk.CTkLabel(payment, text="Payment", text_font=("Arial", 40))  # create heading text
            cc_text = ctk.CTkLabel(form, text="Credit card number:", text_font=("Arial", 20))  # create credit card no text
            sec_code_text = ctk.CTkLabel(form, text="Security code (CVV):", text_font=("Arial", 20))  # create security code text
            address_text = ctk.CTkLabel(form, text="Address", text_font=("Arial", 20))  # create address text
            expiry_text = ctk.CTkLabel(form, text="Expiry date (MM/YY)", text_font=("Arial", 20))  # create expiry date text
            cc = ctk.CTkEntry(form)  # create credit card no text box
            sec_code = ctk.CTkEntry(form)  # create security code text box
            address = ctk.CTkEntry(form)  # create address text box
            expiry = ctk.CTkEntry(form)  # create expiry date text box
            visa_or_mc = tk.StringVar()  # create value to store visa or mastercard value
            visa_or_mc.set("visa")  # set default value to visa
            visa = ctk.CTkRadioButton(form, text="Visa", variable=visa_or_mc, value="visa")  # create visa radio button
            mc = ctk.CTkRadioButton(form, text="Mastercard", variable=visa_or_mc, value="mc")  # create mc radio button
            save_details = tk.IntVar()  # create value to ask whether user wants to save payment details
            save_details.set(0)  # set default value to false
            save = ctk.CTkRadioButton(form, text="Save details", variable=save_details, value=1)  # create save details radio button
            purchase = ctk.CTkButton(form, text="Purchase",
                                     command=lambda: confirm_payment_details(cc.get(),
                                                                             sec_code.get(),
                                                                             expiry.get(),
                                                                             visa_or_mc.get(),
                                                                             address.get(),
                                                                             save_details.get()))  # create purchase button
            heading.pack(padx=30, pady=30)  # place heading text
            cc_text.grid(row=0, column=0, pady=15, sticky="W")  # place credit card no text
            cc.grid(row=0, column=1, pady=15, sticky="E")  # place credit card no text box
            sec_code_text.grid(row=1, column=0, pady=15, sticky="W")  # place security code text
            sec_code.grid(row=1, column=1, pady=15, sticky="E")  # place security code text box
            expiry_text.grid(row=2, column=0, pady=15, sticky="W")  # place expiry date text
            expiry.grid(row=2, column=1, pady=15, sticky="E")  # place expiry date text box
            address_text.grid(row=3, column=0, pady=15, sticky="W")  # place address text
            address.grid(row=3, column=1, pady=15, sticky="E")  # place address text box
            visa.grid(row=4, column=0, pady=15, sticky="E")  # place visa radio button
            mc.grid(row=4, column=1, pady=15, sticky="W")  # place mastercard radio button
            save.grid(row=5, columnspan=2, pady=15)  # place save radio button
            if name == "Payment CC Error":  # error text
                error = ctk.CTkLabel(form, text="Credit card number must be 16 digits", text_color="red")
                error.grid(row=6, columnspan=2, pady=15)
            elif name == "Payment Security Error":  # error text
                error = ctk.CTkLabel(form, text="CVV must be 3 or 4 digits", text_color="red")
                error.grid(row=6, columnspan=2, pady=15)
            elif name == "Payment Expiry Error":  # error text
                error = ctk.CTkLabel(form, text="Expiry date is invalid", text_color="red")
                error.grid(row=6, columnspan=2, pady=15)
            elif name == "Payment VISA/MC Error":  # error text
                error = ctk.CTkLabel(form, text="Must pick either Visa or Mastercard", text_color="red")
                error.grid(row=6, columnspan=2, pady=15)
            elif name == "Payment VISA/MC Error":  # error text
                error = ctk.CTkLabel(form, text="Invalid Address", text_color="red")
                error.grid(row=6, columnspan=2, pady=15)
            purchase.grid(row=7, columnspan=2, pady=15)  # place purchase button
            form.pack()  # place form frame
            payment.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # place payment frame
            left.grid(row=0, column=0, sticky="nswe")  # place top frame
            current_top_frame = left  # set top frame
    elif name == "Confirm payment":
        cart = {}  # set cart to empty after payment
        cart_text.set("0")  # set no of items in cart to 0
        left = ctk.CTkFrame(bottom)  # create top frame
        left.columnconfigure(0, weight=1)  # set width
        left.rowconfigure(0, weight=1)  # set height
        confirmed = ctk.CTkFrame(left)  # create payment confirmed frame
        heading = ctk.CTkLabel(confirmed, text="Payment Confirmed", text_font=("Arial", 50))  # create payment confirmed text
        heading.pack()  # place payment confirmed text
        confirmed.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # place payment confirmed frame
        left.grid(row=0, column=0, sticky="nswe")  # place top frame
        current_top_frame = left  # set top frame
        win.after(3000, lambda: swap_frame("Categories"))  # after 3000ms or 3 seconds, swap frame to categories page
    elif name.startswith("See order"):
        left = ctk.CTkFrame(bottom)  # create top frame
        left.columnconfigure(0, weight=1)  # set width
        left.rowconfigure(0, weight=1)  # set height
        order_frame = ctk.CTkFrame(left)  # create order frame
        heading = ctk.CTkLabel(order_frame, text=f"Order", text_font=("Arial", 40))  # create heading text
        heading.pack(pady=30)  # place heading text
        order = eval(database.fetchone("SELECT * FROM Orders WHERE order_id = ?", (name[10:],))[1])  # get order from database
        thing = ctk.CTkFrame(order_frame)  # create item in order frame
        total_price = 0  # used to calculate total price
        for i, v in enumerate(order):  # grab index and value of item in order
            item = database.fetchone("SELECT * FROM Items WHERE id = ?", (v,))  # get item from database
            name = ctk.CTkLabel(thing, text=item[1], text_font=("Arial", 20))  # create item name text
            times = ctk.CTkLabel(thing, text="x" + str(order[v]), text_font=("Arial", 20))  # create no of items text
            price = ctk.CTkLabel(thing, text=str(item[2] * order[v]), text_font=("Arial", 20))  # create item price text
            total_price += item[2] * order[v]  # multiple no of items with price and add to total price
            name.grid(row=i, column=0, padx=5, pady=5)  # place item name text
            times.grid(row=i, column=1, padx=5, pady=5)  # place no of items text
            price.grid(row=i, column=2, padx=5, pady=5)  # place item price text
        total_label = ctk.CTkLabel(thing, text="Total", text_font=("Arial", 20))  # create total price text
        total_label.grid(row=len(order), column=0, padx=5, pady=5)  # place total price text
        total_price_label = ctk.CTkLabel(thing, text=str(total_price), text_font=("Arial", 20))  # create total price number text
        total_price_label.grid(row=len(order), column=2, padx=5, pady=5)  # place total price number text
        thing.pack()  # place item in grid
        order_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)  # place order frame
        left.grid(row=0, column=0, sticky="nswe")  # place top frame
        current_top_frame = left  # set top frame
    else:
        left = ctk.CTkFrame(bottom)  # create top frame
        left.columnconfigure(0, weight=1, minsize=300)  # set width of left side (picture)
        left.columnconfigure(1, weight=1, minsize=300)  # set width of right side (item details)
        left.rowconfigure(0, weight=1)  # set height
        query = "SELECT * FROM Items WHERE name = ?"
        item = database.fetchone(query, (name,))  # get item details
        url = "https://cdn.discordapp.com/attachments/1024362106264494100/" + item[3]
        img = get_image_thumbnail(url, dim=(400, 400))  # get image from image url
        img_label = ctk.CTkLabel(left, image=img)  # create item image label
        img_label.image = img  # set label's image to item image
        img_label.grid(row=0, column=0, sticky="nswe")  # place item image label
        item_frame = ctk.CTkFrame(left)  # create item details frame
        rating_text = ((5 - int(item[6])) * "☆") + (int(item[6]) * "★")  # find the rating of the item
        no_of_ratings_text = str(int(item[7])) + " ratings"  # find the no. of reviews
        supplier_text = "By " + item[4]  # find the supplier
        price_text = str(int(item[2])) + " QR"  # find the price of the item
        name = ctk.CTkLabel(item_frame, text=item[1], text_font=("Arial", 30), anchor="e")  # create item name text
        rating = ctk.CTkLabel(item_frame, text=rating_text, text_color="yellow", anchor="e", text_font=("Arial", 15))  # create rating text
        no_of_ratings = ctk.CTkLabel(item_frame, text=no_of_ratings_text, text_color="gray", anchor="e",
                                     text_font=("Arial", 15))  # create the no of reviews text
        supplier = ctk.CTkLabel(item_frame, text=supplier_text, text_color="gray", anchor="e", text_font=("Arial", 15))  # create item supplier text
        price = ctk.CTkLabel(item_frame, text=price_text, text_font=("Arial", 23), anchor="e")  # create item price text
        cart_img = get_image_resize(
            "https://cdn.discordapp.com/attachments/1024362106264494100/1024743920225243197/cart.png", dim=(35, 35))  # get cart image
        cart_btn = ctk.CTkButton(item_frame, text="Add to cart", text_font=("Arial", 23), image=cart_img,
                                 command=lambda: add_to_cart(item[0]))  # create add to cart button
        name.pack(fill=tk.X, pady=20)  # place item name text
        rating.pack(fill=tk.X)  # place rating text
        no_of_ratings.pack(fill=tk.X)  # place no of reviews text
        supplier.pack(fill=tk.X)  # place item supplier text
        price.pack(fill=tk.X, pady=20)  # place item price text
        cart_btn.pack(ipadx=5, ipady=5)  # place add to cart button
        item_frame.grid(row=0, column=1, sticky="e")  # place item details frame
        left.grid(row=0, column=0, sticky="nswe")  # place top frame
        current_top_frame = left  # set top frame


# url for the category images
category_img = ("1024377134673821836/electronics.jpg",
                "1024421709689913424/unknown.png",
                "1024377135445573733/furnitures.jpg",
                "1024377135693045781/grocery.png",
                "1024377134405398558/toys.jpg",
                "1024377134002753637/schoolaccessories.jpg")

# names for the categories
category_names = ("Electronics",
                  "Workout Equipment",
                  "Furnitures",
                  "Groceries",
                  "Toys",
                  "School Accessories")

# url for the ad images
ads = ("1026581273088626798/unknown.png",
       "1026581303749005362/unknown.png",
       "1026581368446140426/unknown.png",
       "1026581461429653554/unknown.png",
       "1026581529645821962/unknown.png")

# create ad frame
ad_img = get_image_resize("https://cdn.discordapp.com/attachments/1024362106264494100/" + random.choice(ads),
                          dim=(160, 600))  # get random ad image
ad = ctk.CTkLabel(bottom, image=ad_img)  # create ad image
ad.grid(row=0, column=1, sticky="nswe")  # place ad image

# change to categories frame
swap_frame("Categories")

# create navbar frame
navbar = ctk.CTkFrame(win)
navbar.rowconfigure(0, weight=1)  # set height
navbar.columnconfigure(0, weight=1)  # set width of home button's space
navbar.columnconfigure(1, weight=1)  # set width of title's space
navbar.columnconfigure(2, weight=1, minsize=300)  # set width of account and cart buttons' spaces

# create home button and put in navbar
home = ctk.CTkButton(navbar, text="Home", height=40, width=60, text_font=("Arial", 18),
                     command=lambda: swap_frame("Categories"))
home.grid(row=0, column=0, sticky="w", padx="30")

# create title text and put in navbar
title = ctk.CTkLabel(navbar, text="ShopMart", text_font=("HGPSoeiKakupoptai", 30))
title.grid(row=0, column=1, sticky="nswe")

# create cart button and put in navbar
cart_img = get_image_resize("https://cdn.discordapp.com/attachments/1024362106264494100/1024743920225243197/cart.png",
                            dim=(25, 25))  # get cart image
cart_text = tk.StringVar()  # variable string for the number of items in cart
cart_text.set("0")  # set number of items to 0
cart_btn = ctk.CTkButton(navbar, image=cart_img, width=40, height=40, textvariable=cart_text, text_font=("Arial", 15),
                         command=lambda: swap_frame("Cart"))  # create cart button
cart_btn.grid(row=0, column=2, sticky="e", padx="30")  # place cart button

# create account button and put in navbar
acc_img = get_image_resize("https://cdn.discordapp.com/attachments/1024362106264494100/1024993769013116938/account.png",
                           dim=(25, 25))  # get account image
acc_btn = ctk.CTkButton(navbar, text="", image=acc_img, width=40, height=40, command=lambda: swap_frame("Login"))  # create account button
acc_btn.grid(row=0, column=2, sticky="e", padx="110")  # place account button

# place navbar and bottom frames
navbar.grid(row=0, column=0, sticky="nswe")
bottom.grid(row=1, column=0, sticky="nswe")

# start the app
win.mainloop()
