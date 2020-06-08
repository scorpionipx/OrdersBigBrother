class Config(object):
    SECRET_KEY = "#vai@-09gm$wwv$*gy@xu$&jwi#44h0&rm%^(b%)#*w!07uj*m"
    HOST = "b278a96d287e.ngrok.io"

    SHOPIFY_CONFIG = {
        'API_KEY': 'bbd4918eab1fd4070e055ae17da6f176',
        'API_SECRET': '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',
        'APP_HOME': 'http://' + HOST,
        'CALLBACK_URL': 'http://' + HOST + '/install',
        'REDIRECT_URI': 'http://' + HOST + '/connect',
        'SCOPE': 'read_products, read_collection_listings, read_orders, read_customers',
    }

# "C:\Users\ScorpionIPX\Desktop\ngrok.exe" http 127.0.0.1:8080 -host-header="127.0.0.1:8080"
