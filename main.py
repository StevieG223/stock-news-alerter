import requests
import smtplib
import re
import time
import tkinter

# put in your API key below
ALPHA_VANTAGE_API_KEY='your key'
# put in your API key below
NEWS_API_KEY = "your key"
AV_ENDPOINT = 'https://www.alphavantage.co/query?'
NEWS_API_ENDPOINT = 'https://newsapi.org/v2/everything?'
# put in the 'from' email below. This is the one that will send the alert
MY_EMAIL= 'your email'

# Create GUI to set up user's stocks that they want alerts on
window = tkinter.Tk()
window.title('Stock alerter config')
window.config(padx=20, pady=20)
window.geometry('600x800')

canvas = tkinter.Canvas(width=200, height=200)
stock_img = tkinter.PhotoImage(file='stock_img.png')
canvas.create_image(100, 100, image=stock_img)
canvas.pack()

label = tkinter.Label(text='Stock Alerter', font=18, fg='green')
label.pack()

frame = tkinter.LabelFrame(window, text="Select the Stocks you'd like to follow", padx=20, pady=20)
frame.pack(pady=20, padx=10)

# functions


def check_stocks(stock):
    """
    checks the stock from the pre-exisiting list
    :param stock: stock you'd wish to check
    :return: stock data in json
    """
    global ALPHA_VANTAGE_API_KEY
    result = re.search('\s\(', stock)
    symbol = stock[result.start() +2:-1]
    stock_params = {"function":"TIME_SERIES_DAILY_ADJUSTED",
                    'symbol': symbol,
                    "apikey": ALPHA_VANTAGE_API_KEY,
                    'outputsize': 'compact',
                    'datatype': 'json'
                    }
    response = requests.get(AV_ENDPOINT, params=stock_params)
    response.raise_for_status()
    stock_data = response.json()
    return stock_data


def get_check_inputs(list_of_stocks, vars_list):
    """
    checks the inputs of the stocks listed in the checkboxes, adds them to dict
    :return: list of stocks to check
    """
    check_these_stocks = []
    its = 0
    for var in vars_list:
        if var.get() == 1:
            check_these_stocks.append(list_of_stocks[its])
        its += 1
    return check_these_stocks


def find_dates(stock_dict):
    """
    finds two must recent dates in stock data, yesterday and the day before yesterday
    :param stock_dict: json from alphavantage api
    :return: 2 strings, dates in stock data from yesterday and day before yesterday
    """
    stock_data_keys = list(stock_dict["Time Series (Daily)"].keys())
    data_point_1 = stock_data_keys[1]
    data_point_2 = stock_data_keys[2]
    return data_point_1, data_point_2


def calculate_change(stock_data):
    """
    calculates the percentage of change based on the difference between the two most recent closing prices present in
    the stock data dict. returns the percent change as a float.
    :return: float
    """
    yesterday, day_before_yesterday = find_dates(stock_data)
    day_1_close = float(stock_data['Time Series (Daily)'][day_before_yesterday]["4. close"])
    day_2_close = float(stock_data['Time Series (Daily)'][yesterday]["4. close"])
    change = (1 - (day_1_close/day_2_close)) * 100
    change = round(change, 2)
    return change


def evaluate_change(percent_change):
    """
    evaluates the extent of the change in stock prices, evaluates a change of greater than or equal to 5%
    to be significant
    :param percent_change:float
    :return: boolean
    """
    if percent_change >= 5:
        return True
    elif percent_change <= -5:
        return True
    else:
        return False


def good_news_or_bad(percent_change):
    """
    decides if the change is positive or negative
    :param percent_change: float
    :return: string
    """
    if evaluate_change(percent_change):
        if percent_change >= 5:
            return "Good news!"
        elif percent_change <= -5:
            return "Bad news!"
    else:
        return "No big news"


def get_recent_news(company_name, stock_data):
    """
    uses news api to attempt to find reason for significant stock fluctuation.
    :return: two lists, top 3 most popular headlines list and corresponding urls list
    """
    yesterday, day_before_yesterday = find_dates(stock_data)
    news_params = {
        'q': company_name,
        'from': day_before_yesterday,
        'sortBy': 'popularity',
        'apiKey': 'e905fa62972f40e8a6707b3d45eeba62'}
    news_response = requests.get(NEWS_API_ENDPOINT, params=news_params)
    news_data = news_response.json()
    articles_list = news_data['articles'][0:3]
    headlines_list = [articles_list[0]['title'], articles_list[1]['title'], articles_list[2]['title']]
    urls_list = [articles_list[0]['url'], articles_list[1]['url'], articles_list[2]['url']]
    return headlines_list, urls_list


def create_news(companies_list):
    """
    creates news to later send to email address.
    :param companies_list: companies for which you'll be given news following significant shift
    :return: str, email message to be passed to send function
    """
    email_message = "'Subject:daily stock alerts\n\n'"
    for company in companies_list:
        data = check_stocks(company)
        change = calculate_change(data)
        if evaluate_change(change):
            news = good_news_or_bad(change)
            headlines, urls = get_recent_news(company_name=company, stock_data=data)
            email_message += f"""
            {news} \n
            {company}: {change}%\n
            \t{headlines[0]}\n
            \t{urls[0]}
            \t{headlines[1]}\n
            \t{urls[1]}
            \t{headlines[2]}\n
            \t{urls[2]}\n\n
            ________________________________________________________
                           """
        else:
            news = good_news_or_bad(change)
            email_message += f"""
            {news} \n
            {company}: {change}%\n
            ________________________________________________________"""

        time.sleep(3)
    return email_message


def get_email():
    """
    get email from entry field
    :return: str, email  address
    """
    email_addr = email_entry.get()
    return email_addr


def send_email(email):
    with smtplib.SMTP('smtp.gmail.com', 587, timeout=120) as connection:
        connection.starttls()
        connection.login(user=MY_EMAIL, password='goalqxfzxfjnaood')
        to_email = get_email()
        connection.sendmail(from_addr=MY_EMAIL, to_addrs=to_email,
                            msg=email.encode('utf-8'))
    print('Operation successful!')


def send_alerts():
    """
    final step of the program, sends alerts based on the stocks checked in the tkinter window
    :return: NA
    """
    final_stock_list = get_check_inputs(stocks_for_checks, empty_vars_list)
    email_message = create_news(final_stock_list)
    send_email(email_message)


# create CkBtn class, VarCreator classes


class CkBtn:
    def __init__(self, stock_name, variable):
        stock_name = tkinter.Checkbutton(
            frame, width=30, text=stock_name, anchor='w', variable=variable, onvalue=1, offvalue=0
        )
        stock_name.pack()


class VarCreator:
    def __init__(self):
        super(VarCreator, self).__init__()
        self.empty_vars = []

    def create_vars(self, num_vars):
        its = 0
        var_names = []
        for num in range(0, num_vars):
            var_names.append(f'var{str(its + 1)}')
            its += 1
        for var_name in var_names:
            empty_var = var_name
            empty_var = tkinter.IntVar()
            self.empty_vars.append(empty_var)
        return self.empty_vars


# create checkboxes from CkBtn class, empty vars from VarCreator class
stocks_for_checks = [
    'Apple (AAPL)', 'Tesla (TSLA)', 'Amazon (AMZN)', 'Alphabet Class A (GOOGL)', 'Alphabet Class C (GOOG)',
    'Nvidia Corp. (NVDA)', 'Berkshire Hathaway Inc. (BRK.B)'
]
var_creator = VarCreator()
empty_vars_list = var_creator.create_vars(num_vars=len(stocks_for_checks))

# iterates over the stocks in a list, creating check boxes in the tkinter gui. Will eventually make into function
its = 0
checks = []
for num in range(0, len(stocks_for_checks)):
    check = CkBtn(stock_name=stocks_for_checks[its], variable=empty_vars_list[its])
    checks.append(check)
    its += 1

# create 2nd frame for email entry
frame2 = tkinter.LabelFrame(window, text="enter email to forward alerts", padx=20, pady=20)
frame2.pack(pady=20, padx=10)
email_entry = tkinter.Entry(frame2, width=45)
email_entry.pack()

# create 'send alerts' button
send_button=tkinter.Button(text='send alerts', width=45, command=send_alerts).pack()

window.mainloop()
