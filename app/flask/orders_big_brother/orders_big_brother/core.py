from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, Response, session
# from orders_big_brother.config import Config as CFG
import operator
import requests
import json


class Config(object):
    SECRET_KEY = "#vai@-09gm$wwv$*gy@xu$&jwi#44h0&rm%^(b%)#*w!07uj*m"
    HOST = "31.22.7.200:8080"

    SHOPIFY_CONFIG = {
        'API_KEY': 'bbd4918eab1fd4070e055ae17da6f176',
        'API_SECRET': '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',
        'APP_HOME': 'http://' + HOST,
        'CALLBACK_URL': 'http://' + HOST + '/install',
        'REDIRECT_URI': 'http://' + HOST + '/connect',
        'SCOPE': 'read_products, read_collection_listings, read_orders, read_customers',
    }


CFG = Config()

app = Flask(__name__, template_folder="templates")
app.debug = True
app.secret_key = CFG.SECRET_KEY


START_PER = ''
END_PER = ''

TOTAL = 0
AOV = 0
NOO = 0
MBD = ''


@app.route('/products', methods=['GET'])
def products():
    """ Get a stores products """
    headers = {
        "X-Shopify-Access-Token": session.get("access_token"),
        "Content-Type": "application/json"
    }

    endpoint = "/admin/products.json"
    response = requests.get("https://{0}{1}".format(session.get("shop"),
                                                    endpoint), headers=headers)

    received_products = str(response.content)
    # print('{}'.format(received_products))

    if response.status_code == 200:
        return response
    else:
        return False


class OrderByDate:
    """OrderByDate

    """
    def __init__(self, date, money, noo):
        """__init__

        :param date: date
        :type date: str
        :param money: money
        :type money: float
        :param noo: number of orders
        :type noo: int
        """
        self.date = date
        self.money = money
        self.noo = noo

    @property
    def year(self):
        """year

        :return: year
        """
        year = self.date[:self.date.find('-')]
        # print(year)
        year = int(year)

        return year

    @property
    def month(self):
        """month

        :return: month
        """
        month = self.date[self.date.find('-')+1:]
        month = month[:month.find('-')]
        month = int(month) - 1
        # print(month)
        return month

    @property
    def day(self):
        """month

        :return: month
        """
        day = self.date[self.date.find('-') + 1:]
        day = day[day.find('-') + 1:]
        # print(day)
        day = int(day)
        return day


@app.route('/orders', methods=['GET'])
def orders():
    """ Get a stores orders """
    global START_PER, END_PER, TOTAL, AOV, NOO, MBD

    headers = {
        "X-Shopify-Access-Token": session.get("access_token"),
        "Content-Type": "application/json"
    }

    endpoint = "/admin/api/2020-04/orders.json?status=any&limit=250&fields=id,total-price-set,created-at,number"
    response = requests.get("https://{0}{1}".format(session.get("shop"), endpoint), headers=headers)

    received_orders = response.content.decode('utf-8')
    # print(received_orders)

    orders_js = json.loads(received_orders)

    orders = orders_js['orders']
    orders = list(orders)

    start_date = '{}'.format(orders[-1]['created_at'])
    end_date = '{}'.format(orders[0]['created_at'])
    total = 0
    for order in orders:
        # print('{}: {}'.format(order['id'], order['total_price_set']['shop_money']['amount']))
        total += float(order['total_price_set']['shop_money']['amount'])

    print('PERIOD: {} - {}'.format(start_date, end_date))
    START_PER = start_date
    END_PER = end_date
    print('total: {}RON'.format(total))
    TOTAL = total
    print('aov: {:.2f}RON'.format(total / len(orders)))
    AOV = total / len(orders)
    print('ORDERS: {}'.format(len(orders)))
    NOO = len(orders)

    orders_by_date = {}
    money_by_date = {}
    for order in orders:
        date = order['created_at']
        date = date[:date.find('T')]
        if orders_by_date.get(date, None):
            orders_by_date[date] += 1
        else:
            orders_by_date[date] = 1

        if money_by_date.get(date, None):
            money_by_date[date] += float(order['total_price_set']['shop_money']['amount'])
        else:
            money_by_date[date] = float(order['total_price_set']['shop_money']['amount'])

    mbd = []
    for k, v in money_by_date.items():
        mbd_obj = OrderByDate(
            date=k,
            money=v,
            noo=0,
        )
        mbd.append(mbd_obj)

    index = 0
    for k, v in orders_by_date.items():
        mbd[index].noo = v
        index += 1
    mbd.reverse()
    MBD = mbd

    # for o in mbd:
    #     print('{}: {}'.format(o.date, o.money))

    # print('DATES:\n{}'.format(orders_by_date))
    # print('MONEY:\n{}'.format(money_by_date))

    if response.status_code == 200:
        return response
    else:
        return False


class Customer:
    """Customer

    """
    def __init__(self, pk, state, total_spent, orders_count, currency):
        """__init__

        :param pk: pk
        :type pk: int
        :param state: state
        :type state: str
        :param total_spent: total_spent
        :type total_spent: float
        :param orders_count: orders_count
        :type orders_count: int
        :param currency: currency
        :type currency: str
        """
        self.pk = pk
        self.state = state
        self.total_spent = total_spent
        self.orders_count = orders_count
        self.currency = currency


@app.route('/customers', methods=['GET'])
def get_customers():
    """ get_customers

    """
    headers = {
        "X-Shopify-Access-Token": session.get("access_token"),
        "Content-Type": "application/json"
    }

    fields = (
        'id',
        'total-spent',
        'orders-count',
        'state',
        'currency',
    )
    slugify_fields = ",".join(fields)

    last_id = 0
    customer_count = 250

    raw_customers = []

    while customer_count == 250:
        endpoint = "/admin/api/2020-04/customers.json?fields={}&limit=250&orders_count_min=1&since_id={}"\
            .format(slugify_fields, last_id)
        print(endpoint)
        response = requests.get("https://{0}{1}".format(session.get("shop"),
                                                        endpoint), headers=headers)

        received_customers = response.content.decode('utf-8')
        # print(received_orders)

        try:
            customers_js = json.loads(received_customers)

            session_customers = customers_js['customers']
            session_customers = list(session_customers)
            last_id = session_customers[-1]['id']
            customer_count = len(session_customers)
            raw_customers.extend(session_customers)

        except Exception as exception:
            print(exception)
            print(received_customers)
            break

    print('CUSTOMERS: {}'.format(len(raw_customers)))
    customers = []
    for raw_customer in raw_customers:
        customer = Customer(
            pk=int(raw_customer['id']),
            state='{}'.format(raw_customer['state']),
            total_spent=float(raw_customer['total_spent']),
            orders_count=int(raw_customer['orders_count']),
            currency='{}'.format(raw_customer['currency'])
        )
        customers.append(customer)

    customers = sorted(customers, key=operator.attrgetter('total_spent'))
    customers.reverse()
    return customers


@app.route('/install', methods=['GET'])
def install():
    """
    Connect a shopify store
    """
    shop = request.args.get('shop', None)
    if not shop:
        return Response(response="Error: parameter shop not found", status=500)

    auth_url = "https://{}/admin/oauth/authorize?client_id={}&scope={}&redirect_uri={}"\
        .format(shop, CFG.SHOPIFY_CONFIG["API_KEY"], CFG.SHOPIFY_CONFIG["SCOPE"], CFG.SHOPIFY_CONFIG["REDIRECT_URI"])

    return redirect(auth_url)


@app.route('/connect', methods=['GET'])
def connect():
    view_name = 'home'
    if request.args.get("shop"):
        data = {
            "client_id": CFG.SHOPIFY_CONFIG["API_KEY"],
            "client_secret": CFG.SHOPIFY_CONFIG["API_SECRET"],
            "code": request.args.get("code")
        }

        auth_link = "https://{0}/admin/oauth/access_token".format(request.args.get("shop"))
        resp = requests.post(
            url=auth_link,
            data=data,
        )

        if 200 == resp.status_code:
            resp_json = json.loads(resp.text)

            session['access_token'] = resp_json.get("access_token")
            session['shop'] = request.args.get("shop")

            return render_template('main_menu.html', view_name=view_name)
        else:
            print("Failed to get access token: ", resp.status_code, resp.text)
            return render_template('error.html')


def get_orders():
    """get_orders

    :return:
    """
    orders = []
    return orders


def get_money_by_day():
    """get_money_by_day

    :return:
    """
    headers = {
        "X-Shopify-Access-Token": session.get("access_token"),
        "Content-Type": "application/json"
    }

    endpoint = "/admin/api/2020-04/orders.json?status=any&limit=250&fields=id,total-price-set,created-at,number"
    response = requests.get("https://{0}{1}".format(session.get("shop"), endpoint), headers=headers)

    received_orders = response.content.decode('utf-8')
    orders_js = json.loads(received_orders)

    orders = orders_js['orders']
    orders = list(orders)

    total = 0
    for order in orders:
        total += float(order['total_price_set']['shop_money']['amount'])

    orders_by_date = {}
    money_by_date = {}
    for order in orders:
        date = order['created_at']
        date = date[:date.find('T')]
        if orders_by_date.get(date, None):
            orders_by_date[date] += 1
        else:
            orders_by_date[date] = 1

        if money_by_date.get(date, None):
            money_by_date[date] += float(order['total_price_set']['shop_money']['amount'])
        else:
            money_by_date[date] = float(order['total_price_set']['shop_money']['amount'])

    mbd = []
    for k, v in money_by_date.items():
        mbd_obj = OrderByDate(
            date=k,
            money=v,
            noo=0,
        )
        mbd.append(mbd_obj)

    index = 0
    for k, v in orders_by_date.items():
        mbd[index].noo = v
        index += 1
    mbd.reverse()
    return mbd


@app.route('/money_by_day', methods=['GET'])
def money_by_day():
    """money_by_day

    :return:
    """
    mbd = get_money_by_day()
    return render_template('money_by_day.html', mbd=mbd)


def get_may_orders():
    """get_may_orders

    :return:
    """
    may_orders = []
    total = 0

    headers = {
        "X-Shopify-Access-Token": session.get("access_token"),
        "Content-Type": "application/json"
    }

    endpoint = "/admin/api/2020-04/orders.json?status=any&limit=250&fields=id,total-price-set,created-at,number,line_items&since_id=2153476259884"
    response = requests.get("https://{0}{1}".format(session.get("shop"), endpoint), headers=headers)

    received_orders = response.content.decode('utf-8')
    orders_js = json.loads(received_orders)
    orders = orders_js['orders']
    orders = list(orders)

    for order in orders:
        products = list(order['line_items'])
        total += len(products)
        may_order = '{} - {} - {}'.format(order['id'], order['created_at'], len(products))
        may_orders.append(may_order)

    endpoint = "/admin/api/2020-04/orders.json?status=any&limit=67&fields=id,total-price-set,created-at,number,line_items&since_id=2477755400353"
    response = requests.get("https://{0}{1}".format(session.get("shop"), endpoint), headers=headers)

    received_orders = response.content.decode('utf-8')
    orders_js = json.loads(received_orders)
    orders = orders_js['orders']
    orders = list(orders)

    for order in orders:
        products = list(order['line_items'])
        total += len(products)
        may_order = '{} - {} - {}'.format(order['id'], order['created_at'], len(products))
        may_orders.append(may_order)

    return may_orders, total


@app.route('/may', methods=['GET'])
def may():
    """may

    :return:
    """
    may_orders, total = get_may_orders()
    return render_template('may.html', may_orders=may_orders, total=total)


def get_financial_status_by_payment_gateway_names(orders):
    """get_financial_status_by_payment_gateway_names

    :param orders: orders
    :return:
    """
    financial_status = {
        'authorized': {
            'value': 0,
            'orders': 0,
        },
        'pending': {
            'value': 0,
            'orders': 0,
        },
        'paid': {
            'value': 0,
            'orders': 0,
        },
        'partially_paid': {
            'value': 0,
            'orders': 0,
        },
        'refunded': {
            'value': 0,
            'orders': 0,
        },
        'voided': {
            'value': 0,
            'orders': 0,
        },
        'partially_refunded': {
            'value': 0,
            'orders': 0,
        },
        'unpaid': {
            'value': 0,
            'orders': 0,
        },
    }

    payment_gateway_names = {}
    for order in orders:
        if payment_gateway_names.get(order.payment, None):
            pass
        else:
            payment_gateway_names[order.payment] = {
                    'authorized': {
                        'value': 0,
                        'orders': 0,
                    },
                    'pending': {
                        'value': 0,
                        'orders': 0,
                    },
                    'paid': {
                        'value': 0,
                        'orders': 0,
                    },
                    'partially_paid': {
                        'value': 0,
                        'orders': 0,
                    },
                    'refunded': {
                        'value': 0,
                        'orders': 0,
                    },
                    'voided': {
                        'value': 0,
                        'orders': 0,
                    },
                    'partially_refunded': {
                        'value': 0,
                        'orders': 0,
                    },
                    'unpaid': {
                        'value': 0,
                        'orders': 0,
                    },
            }
        payment_gateway_names[order.payment][order.financial_status]['value'] += order.value
        payment_gateway_names[order.payment][order.financial_status]['orders'] += 1

    for k, v in payment_gateway_names.items():
        for i, j in v.items():
            print(j)

    return payment_gateway_names


def get_orders_from_interval(start, end):
    """get_orders_from_interval

    :param start: start of interval
    :type start: str
    :param end: end of interval
    :type end: str

    :return: orders from the interval
    :rtype: list
    """
    class IntervalOrder:
        """IntervalOrder

        """
        def __init__(self, pk, created_at, value, currency, number_of_products, payment, financial_status, ):
            """__init__

            :param pk: pk
            :type pk: int
            :param created_at: created_at
            :type created_at: str
            :param value: value
            :type value: float
            :param currency: currency
            :type currency: str
            :param number_of_products: number_of_products
            :type number_of_products: int
            """
            self.pk = pk
            self.created_at = created_at
            self.value = value
            self.currency = currency
            self.number_of_products = number_of_products
            self.payment = payment
            self.financial_status = financial_status

    print('getting orders from interval: {} - {}'.format(start, end))
    headers = {
        "X-Shopify-Access-Token": session.get("access_token"),
        "Content-Type": "application/json"
    }

    api_version = '/admin/api/2020-04'

    fields = [
        'id',
        'created-at',
        'currency',
        'total_price',
        'line_items',
        'payment_gateway_names',
        'financial_status',
    ]
    query_limit = 250
    orders_count = query_limit
    slugify_fields = ",".join(fields)

    last_id = 0

    fetched_orders = []

    fetch_count = 0

    start_dt = datetime.strptime(start, '%Y-%m-%d') - timedelta(hours=3)

    start_year = int(start_dt.year)
    start_month = '{:02d}'.format(int(start_dt.month))
    start_day = '{:02d}'.format(int(start_dt.day))

    end_dt = datetime.strptime(end, '%Y-%m-%d')
    end_year = int(end_dt.year)
    end_month = '{:02d}'.format(int(end_dt.month))
    end_day = '{:02d}'.format(int(end_dt.day))

    # start_period = 'processed_at_min={}-{}-{}T00:00:00+03:00'.format(start_year, start_month, start_day)
    start_period = 'processed_at_min={}-{}-{}T21:00:00'.format(start_year, start_month, start_day)
    # start_period = 'created_at_min=2020-06-01T00:00:00'
    print(start_period)
    end_period = 'created_at_max={}-{}-{}T21:00:00'.format(end_year, end_month, end_day)
    print(end_period)

    while orders_count == query_limit:
        fetch_count += 1
        print('Fetch count: {}'.format(fetch_count))

        endpoint = '{}/orders.json?status=any&limit={}&fields={}&since_id={}&{}&{}'\
            .format(api_version, query_limit, slugify_fields, last_id, start_period, end_period)
        full_link = "https://{0}{1}".format(session.get("shop"), endpoint)
        response = requests.get(full_link, headers=headers)

        raw_orders = response.content.decode('utf-8')
        print('RAW ORDERS:\n{}'.format(raw_orders))
        print('LAST_ID: {}'.format(last_id))

        try:
            orders_js = json.loads(raw_orders)
            orders_list = list(orders_js['orders'])
            orders_count = len(orders_list)
            for order in orders_list:
                order_products = list(order['line_items'])
                products_count = len(order_products)
                del order_products
                entry = IntervalOrder(
                    pk=int(order['id']),
                    created_at=order['created_at'],
                    value=float(order['total_price']),
                    currency=order['currency'],
                    number_of_products=products_count,
                    payment=order['payment_gateway_names'][-1],
                    financial_status=order['financial_status'],
                )
                fetched_orders.append(entry)
        except Exception as exception:
            print('Error fetching orders! {}'.format(exception))
            orders_count = 0
        last_id = fetched_orders[-1].pk

    print('got the orders, boss! {}'.format(len(fetched_orders)))
    return fetched_orders


@app.route('/products_sold_by_period', methods=['GET', 'POST'])
def products_sold_by_period_init():
    """may

    :return:
    """
    view_name = 'products_sold_by_period'

    orders_from_interval = []
    number_of_orders = 0
    total_value = 0
    total_number_of_products = 0
    payment_gateways = {}

    start = 'N/A'
    end = 'N/A'

    if request.method == 'POST':
        # print('POSTING')
        start_period = request.form.get('period-start')
        end_period = request.form.get('period-end')

        orders_from_interval = get_orders_from_interval(start_period, end_period)

        if orders_from_interval:
            start = orders_from_interval[0].created_at
            end = orders_from_interval[-1].created_at

        number_of_orders = len(orders_from_interval)
        for order_from_interval in orders_from_interval:
            total_value += order_from_interval.value
            total_number_of_products += order_from_interval.number_of_products

        total_value = round(total_value, 2)

        payment_gateways = get_financial_status_by_payment_gateway_names(orders_from_interval)
        print(payment_gateways)

    if request.method == 'GET':
        # print('GETTING')
        pass

    return render_template('products_sold_by_period.html', view_name=view_name,
                           orders_from_interval=orders_from_interval,
                           number_of_orders=number_of_orders,
                           total_value=total_value,
                           total_number_of_products=total_number_of_products,
                           start=start,
                           end=end,
                           payment_gateways=payment_gateways,
                           )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
