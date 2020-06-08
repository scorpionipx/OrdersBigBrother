import logging

import json

import requests

from django.http import HttpResponse, HttpResponseServerError

from django.shortcuts import redirect

from django.views import generic


LOGGER = logging.getLogger('Home')

LOGGER.info('Hello')
LOGGER.setLevel(logging.INFO)

console = logging.StreamHandler()
LOGGER.addHandler(console)


class Config(object):
    SECRET_KEY = "#vai@-09gm$wwv$*gy@xu$&jwi#44h0&rm%^(b%)#*w!07uj*m"
    HOST = "452a7811a2c0.ngrok.io"

    SHOPIFY_CONFIG = {
        'API_KEY': 'bbd4918eab1fd4070e055ae17da6f176',
        'API_SECRET': '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',
        'APP_HOME': 'http://' + HOST,
        'CALLBACK_URL': 'http://' + HOST + '/install',
        'REDIRECT_URI': 'http://' + HOST + '/connect',
        'SCOPE': 'read_products, read_collection_listings, read_orders, read_customers',
    }


cfg = Config()


class HomePageView(generic.TemplateView):
    """HomePageView

    """
    template_name = 'home.html'


class InstallView(generic.View):
    """InstallView

    """
    @staticmethod
    def get(request, *args, **kwargs):
        """get

        :param request:
        :param args:
        :param kwargs:
        :return:
        """
        LOGGER.info('\nInstalling..')
        shop = request.GET.get('shop', None)
        LOGGER.info('SHOP: {}'.format(shop))
        if shop:
            pass
        else:
            html = '<html><body>Could not find the shop!</body></html>'
            return HttpResponse(html)

        auth_url = "https://{0}/admin/oauth/authorize?client_id={1}&scope={2}&redirect_uri={3}".format(
            shop, cfg.SHOPIFY_CONFIG["API_KEY"], cfg.SHOPIFY_CONFIG["SCOPE"],
            cfg.SHOPIFY_CONFIG["REDIRECT_URI"]
        )
        LOGGER.info("\n\nDebug - auth URL: {}\n\n".format(auth_url))
        return redirect(auth_url)


class ConnectView(generic.TemplateView):
    """ConnectView

    """
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        LOGGER.info('\n\nConnected')

        LOGGER.info('\n\nKWARGS:\n')
        for k, v in request.GET.items():
            LOGGER.info('{}: {}'.format(k.upper(), v))
        LOGGER.info('\n\n')

        shop = request.GET.get('shop', None)
        code = request.GET.get('code', None)

        LOGGER.info('\nCODE: {}\n'.format(code))

        if shop:
            params = {
                "client_id": cfg.SHOPIFY_CONFIG["API_KEY"],
                "client_secret": cfg.SHOPIFY_CONFIG["API_SECRET"],
                "code": code,
            }

            LOGGER.info('getting access token....')

            resp = requests.post(
                "https://{0}/admin/oauth/access_token".format(
                    shop
                ),
                data=params,
            )

            if 200 == resp.status_code:

                resp_json = json.loads(resp.text)

                html = '<html><body>FROM SHOPY: {}</body></html>'.format(resp_json)

                access_token = resp_json.get('access_token')
                LOGGER.info('\n\nACCESS TOKEN: {}\n\n'.format(access_token))
                request.session['shop'] = shop
                request.session['access_token'] = access_token

                LOGGER.info('returning HttpResponse...\n\n{}\n\n'.format(request.session['shop']))

                headers = {
                    "X-Shopify-Access-Token": access_token,
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
                endpoint = "/admin/api/2020-04/customers.json?fields={}&limit=250&orders_count_min=1&since_id={}" \
                    .format(slugify_fields, last_id)
                response = requests.get("https://{0}{1}".format(shop, endpoint), headers=headers)

                received_customers = response.content.decode('utf-8')
                print('{}'.format(received_customers))

                return HttpResponse(html)
            else:
                html = '<html><body>failed to get response</body></html>'
                return HttpResponse(html)
                # print("Failed to get access token: ", resp.status_code, resp.text)
                # return render_template('error.html')
        LOGGER.info('returning super...')
        return super().get(request, *args, **kwargs)
