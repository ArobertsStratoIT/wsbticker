import praw
import json
import pprint
from datetime import datetime
import time
import threading
import tkinter as tk
from yahoofinancials import YahooFinancials
from tkinter import *
import webbrowser
import configparser
import os
from os import path
import tkinter.messagebox


config = configparser.ConfigParser()
config.read('wsbt_config.ini')

if not path.exists("praw.ini"):
    tkinter.messagebox.showerror("Error", "The praw.ini file is not found. Please redownload the application.")
    os._exit(1)

if not path.exists("gripbar.gif"):
    tkinter.messagebox.showerror("Error", "The gripbar.gif file is not found. Please redownload the application.")
    os._exit(1)
    


if 'SETTINGS' in config:
    if 'screen_width' in config['SETTINGS']:
        screen_width = int(config['SETTINGS']['screen_width'])

    if 'stocks' in config['SETTINGS']:
        stocks = config['SETTINGS']['stocks']
        stocks = [x.strip() for x in stocks.split(',')]

    if 'font_size' in config['SETTINGS']:
        font_size = int(config['SETTINGS']['font_size'])

    if 'theme' in config['SETTINGS']:
        theme = config['SETTINGS']['theme']

try: screen_width 
except NameError: screen_width = 1920

try: stocks 
except NameError: stocks = ['AAPL', 'MSFT', 'LYFT', 'TSLA', 'GOOGL']

try: theme 
except NameError: theme = 'blue'
if theme not in ['blue', 'black', 'white', 'mods']:
    theme = 'blue'

try: font_size 
except NameError: font_size = 20


themecolors = {}
themecolors['blue'] = {'bg' : 'blue', 'fg' : 'white', 'user' : '#90ee90', 'mods' : 'pink'}
themecolors['black'] = {'bg' : 'black', 'fg' : 'gold', 'user' : '#90ee90', 'mods' : 'pink'}
themecolors['white'] = {'bg' : 'white', 'fg' : 'black', 'user' : 'green', 'mods' : 'pink'}
themecolors['mods'] = {'bg' : 'pink', 'fg' : 'yellow', 'user' : 'green', 'mods' : 'red'}



stock_dict = {}
comment_dict = {}
comments_in_queue = 0
ticker_paused = 0
tick_rate = 100
old_comments = []
stickies = []
mod_list = []





reddit = praw.Reddit(user_agent='WSB Ticker',
                     client_id='IniTKSLJs8hlfg', client_secret=None)


class App(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.floater = FloatingWindow(self)

class FloatingWindow(tk.Toplevel):
    def __init__(self, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.overrideredirect(True)
        path = "gripbar.gif"
        self.gripbar = tk.PhotoImage(file=path)
        
        #self.label = tk.Label(self, text="Click on the grip to move")
        self.grip = tk.Label(self, image=self.gripbar, width=25, height=25)
        self.grip.pack_propagate(0)
        self.grip.pack(side="left", fill="y")
        #self.label.pack(side="right", fill="both", expand=True)

        self.grip.bind("<ButtonPress-1>", self.StartMove)
        self.grip.bind("<ButtonRelease-1>", self.StopMove)
        self.grip.bind("<B1-Motion>", self.OnMotion)

        self.popup_menu = tk.Menu(self, tearoff=0)
        
        self.popup_menu.add_command(label="Pause", command=self.pauseTicker)
        self.popup_menu.add_command(label="Resume", command=self.resumeTicker)


        self.speed_submenu = tk.Menu(self.popup_menu)
        self.speed_submenu.add_command(label="Slow", command=lambda: self.setSpeed(200))
        self.speed_submenu.add_command(label="Med", command=lambda: self.setSpeed(100))
        self.speed_submenu.add_command(label="Fast", command=lambda: self.setSpeed(50))
        self.popup_menu.add_cascade(label='Tick Speed', menu=self.speed_submenu, underline=0)

        self.theme_submenu = tk.Menu(self.popup_menu)
        self.theme_submenu.add_command(label="Blue", command=lambda: self.setTheme('blue'))
        self.theme_submenu.add_command(label="Black", command=lambda: self.setTheme('black'))
        self.theme_submenu.add_command(label="White", command=lambda: self.setTheme('white'))
        self.theme_submenu.add_command(label="Mods", command=lambda: self.setTheme('mods'))
        self.popup_menu.add_cascade(label='Theme', menu=self.theme_submenu, underline=0)

        self.popup_menu.add_command(label="Close",
                                    command=self.destroy_root)

        self.bind("<Button-3>", self.popup) # Button-2 on Aqua

    def StartMove(self, event):
        self.x = event.x
        self.y = event.y

    def StopMove(self, event):
        self.x = None
        self.y = None

    def OnMotion(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.winfo_x() + deltax
        y = self.winfo_y() + deltay
        self.geometry("+%s+%s" % (x, y))

    
    def popup(self, event):
        try:
            self.popup_menu.tk_popup(event.x_root, event.y_root, 0)
        finally:
            self.popup_menu.grab_release()

    def destroy_root(self):
        global root
        root.quit()
        root.destroy()
        os._exit(1)

    def pauseTicker(self):
        global ticker_paused
        ticker_paused = 1

    def resumeTicker(self):
        global ticker_paused
        ticker_paused = 0

    def setSpeed(self, ts):
        global tick_rate
        tick_rate = ts

    def setTheme(self, new_theme):
        global theme
        theme = new_theme
        marquee.config(bg=themecolors[theme]['bg'], fg=themecolors[theme]['fg'])
        

        



def showLink(event):
     webbrowser.open(event.widget.tag_names(CURRENT)[1])

def printLink(event):
    print(event.widget.tag_names(CURRENT)[1])



root = App()


root.withdraw()
f = Frame(root.floater, height=font_size*1.4, width=screen_width-32)
root.floater.geometry("+0+800")
f.pack_propagate(0) # don't shrink
f.pack()
marquee = Text(f, bg=themecolors[theme]['bg'], fg=themecolors[theme]['fg'],font=("Lucida Console", font_size))
#marquee.bind("<Button-1>", showLink)
marquee.pack(fill=BOTH, expand=1)
root.floater.wm_attributes("-topmost", 1)







i = 0

def check_stickies():
    global stickies
    global stream
    stickies = []
    for submission in reddit.subreddit('wallstreetbets').hot(limit=5):
        if submission.stickied:
            stickies.append('t3_' +submission.id)
    time.sleep(300)

def get_mods():
    global mod_list
    for moderator in reddit.subreddit('wallstreetbets').moderator():
        mod_list.append(moderator)
    
    

def create_ticker(i):
    global stream
    global ticker_paused
    global mod_list
    if not ticker_paused:
        cursor_position = 0
        marquee.delete('1.0', END)
        comment_count = 0
        
        #Trim comment dict if it gets too long
        if len(comment_dict) > 100:
            print("Trimming comments")
            for index, comment in enumerate(list(comment_dict)):
                if index > 10 and index % 2 != 0:
                    del comment_dict[comment]
                
        for comment in list(comment_dict):
            if cursor_position < (screen_width/10):
                if len(comment_dict[comment]['author']) > 0 or len(comment_dict[comment]['body']) > 0:
                    if len(comment_dict[comment]['author']) > 0:
                        if comment_dict[comment]['original_author'] in  mod_list:                            
                            marquee.insert("1."+str(cursor_position), comment_dict[comment]['author'], ('author_is_mod', comment_dict[comment]['author_link']))
                        else:
                            marquee.insert("1."+str(cursor_position), comment_dict[comment]['author'], ('author', comment_dict[comment]['author_link']))
                        #marquee.tag_add("start", "1."+str(cursor_position), "1."+str(cursor_position + len(comment_dict[comment]['author'])))
                        cursor_position += len(comment_dict[comment]['author'])
                        marquee.insert("1."+str(cursor_position), comment_dict[comment]['body'], ('link', str(comment_dict[comment]['link'])))
                        cursor_position += len(comment_dict[comment]['body'])
                        
                    else:
                        marquee.insert("1."+str(cursor_position), comment_dict[comment]['body'], ('link', str(comment_dict[comment]['link'])))
                        cursor_position += len(comment_dict[comment]['body'])
                        
                    if comment_count == 0:
                        comment_count+=1
                        if len(comment_dict[comment]['author']) >0:
                            comment_dict[comment]['author'] = comment_dict[comment]['author'][1:]
                        else:
                            comment_dict[comment]['body'] = comment_dict[comment]['body'][1:]
                else:
                    del comment_dict[comment]
                    
        marquee.tag_bind('link', '<Button-1>', showLink)
        marquee.tag_bind('author', '<Button-1>', showLink)
        marquee.tag_config("author", foreground=themecolors[theme]['user'])
        marquee.tag_config("author_is_mod", foreground=themecolors[theme]['mods'])
        
    root.after(tick_rate, lambda:create_ticker(i))

def get_comments():
    print("updating")
    global stream
    global old_comments
    global comment_dict
    global comments_in_queue
    comment_dict['welcome'] = {}
    comment_dict['welcome']['author'] = "                                                                                                 /u/MSMSP: "
    comment_dict['welcome']['author_link'] = "https://old.reddit.com/u/MSMSP"
    comment_dict['welcome']['original_author'] = ""
    comment_dict['welcome']['link'] = "https://old.reddit.com/r/wallstreetbets"
    comment_dict['welcome']['created_utc'] = ''
    comment_dict['welcome']['body'] = " Welcome to the /r/Wallstreetbets Ticker! Now loading comments and stock prices..... ###"
    for comment in reddit.subreddit('wallstreetbets').stream.comments():
        if hasattr(comment, 'body') and comment.created_utc > (time.time() -300) and comment.id not in old_comments and comment.link_id in stickies:
            old_comments.append(comment.id)
            body = comment.body.replace("\r"," ")
            body = body.replace("\n"," ")
            body = body.strip()
            for stock in stocks:
                if stock in stock_dict:
                    if stock in body:
                        #print("Found stock ticker!")
                        if stock_dict[stock]['regularMarketChangePercent'] > 0:
                            body = body.replace(stock, stock + " (" + str(stock_dict[stock]['regularMarketPrice']) + " ⮝" +str(round(stock_dict[stock]['regularMarketChangePercent']*100,2)) + "%" ") ")
                        else:
                            body = body.replace(stock, stock + " (" + str(stock_dict[stock]['regularMarketPrice']) + " ⮟" +str(round(stock_dict[stock]['regularMarketChangePercent']*100,2)) + "%" ") ")
            comment_dict[comment.id] = {}
            comment_dict[comment.id]['author'] = " /u/" + str(comment.author) + ": "
            comment_dict[comment.id]['original_author'] = str(comment.author)
            comment_dict[comment.id]['author_link'] = "https://old.reddit.com/u/" + str(comment.author)
            comment_dict[comment.id]['link'] = comment.link_permalink + comment.id
            comment_dict[comment.id]['created_utc'] = comment.created_utc
            if len(body) < 500:
                comment_dict[comment.id]['body'] = body + " ###"
            else:
                comment_dict[comment.id]['body'] = body[0:500] + "... blah blah blah ###"
                #print("blabber detected!")

            
            #print(body[:10]+"...")
            comments_in_queue = len(comment_dict)
            #print(comments_in_queue)


def find_all(a_str, sub):
    start = 0
    while True:
        start = a_str.find(sub, start)
        if start == -1: return
        yield start
        end = a_str.find(':', start)
        yield end
        start += len(sub)

def get_stock_prices():
    global stock_dict
    global stream
    while True:
        print("#### UPDATING STOCK PRICES")
        current = YahooFinancials(stocks)
        stock_dict = current.get_stock_price_data()
        print("#### DONE UPDATING STOCK PRICES")
        time.sleep(600)


get_mods()
    
if __name__ == '__main__':
    threading.Thread(target=check_stickies).start()
    threading.Thread(target=get_comments).start()
    threading.Thread(target=get_stock_prices).start()
    create_ticker(i)
    root.mainloop()
