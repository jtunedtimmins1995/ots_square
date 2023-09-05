import streamlit as st
import pandas as pd
import numpy as np
from google_sheets import *
import streamlit_authenticator as stauth

from boto import get_square_secret
from square.client import Client
import os
import yaml
from yaml.loader import SafeLoader

col1, col2 = st.columns([1,5],gap='small')






with col1:   
    st.image(
                "https://oldthorntoniansfc.com/wp-content/uploads/2021/02/Old-Thorntonians-Crest-2014_150dpi.png",
                width=100, # Manually Adjust the width of the image as per requirement
            )
with col2:
    st.title('OTs Square Automation')


with open('st_creds.yaml', 'r') as file:
    config = yaml.safe_load(file)
    
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
    )

name, authentication_status, username = authenticator.login('Login', 'main')


if authentication_status:
    authenticator.logout('Logout', 'main')
    st.write(f'Welcome *{name}*')
    option = st.selectbox(
        'Automation Type:',
        ('Get New Payments', 'Generate Match Invoices'))


    if option == 'Get New Payments':

        SAMPLE_SPREADSHEET_ID_input = '1K_uXqI1eiguBMr0uH3Tu7xDzePAIi3uAsDrAWukyBq8'
        SAMPLE_RANGE_NAME = 'Square Subs!A:G'

            
        def get_value(key1,key2):
            try:
                return key1[key2] 
            except:
                return None
            
        def google_sheet_func(SAMPLE_SPREADSHEET_ID_input, SAMPLE_RANGE_NAME):
            return get_spread_sheet(SAMPLE_SPREADSHEET_ID_input, SAMPLE_RANGE_NAME)

        def get_most_recent_sub_date(df):
            dates = df[df['Date'].str.contains('T')]

            most_recent_transaction_date = pd.to_datetime(dates['Date'], format='mixed').max().isoformat()

            return most_recent_transaction_date

        def get_payments(first_date, exist):
            
            client = Client(
                access_token=get_square_secret()['SQUARE_ACCESS_TOKEN'],
                environment='production')
            
            orders_api = client.orders
            customers_api = client.customers
            invoices_api = client.invoices

            body = {
            'location_ids': [
                'SBBJSGR24YHYB'
            ],
            'query': {
                'filter': {
                    
                    'date_time_filter': {
                        'updated_at': {
                            'start_at': f'{first_date}',
                        }
                    },
            },
            "sort": {
            "sort_field": "UPDATED_AT",
            "sort_order": "DESC"
            }
                
            },
        }
            
            s_orders = orders_api.search_orders(body).body['orders']

            


            result = invoices_api.list_invoices(
                'SBBJSGR24YHYB'
            )

            invoices = pd.DataFrame(result.body['invoices'])

            # i=1
            while result.cursor:
                # print(i)
                # i+=1
                result = invoices_api.list_invoices(
                    'SBBJSGR24YHYB',
                    cursor = result.cursor
                )
            invoices = pd.concat([invoices, pd.DataFrame(result.body['invoices'])])

            orders_format = []
            for i, order in enumerate(s_orders[:]):
                
                # print(i, '/', len(s_orders))
                new_order = {}
                
                new_order['id']=get_value(order,'id')
                new_order['created_at']=get_value(order,'updated_at')
                
                new_order['customer_id']=get_value(order,'customer_id')
                
                new_order['state']=get_value(order,'state')

                new_order['tenders']=get_value(order,'tenders')

                if not new_order['customer_id']:
                    customer_ids = []
                    try:
                        for tender in order['tenders']:
                            if get_value(tender,'customer_id'):
                                customer_ids.append(get_value(tender,'customer_id'))
                        new_order['customer_id'] = customer_ids[0]
                    except:
                        pass

                if new_order['customer_id']:
                    customer = customers_api.retrieve_customer(new_order['customer_id'])
                
                    try:
                        new_order['first_name'] = get_value(customer.body['customer'],'given_name')
                        new_order['last_name'] = get_value(customer.body['customer'],'family_name')
                    except:
                        print(customer.body)
                else:
                    pass
                    invoice = invoices[invoices['order_id']==new_order['id']]
                    
                    
                    if len(invoice)>0:
                        cust_id = list(invoice['primary_recipient'])[0]['customer_id']
                        customer = customers_api.retrieve_customer(cust_id)
                        try:
                            new_order['first_name'] = get_value(customer.body['customer'],'given_name')
                            new_order['last_name'] = get_value(customer.body['customer'],'family_name')
                        except:
                            print(customer.body)
                        
                for item in order['line_items']:
                    line_dict = new_order.copy()
                    
                    line_dict['variation_name']=get_value(item,'variation_name')
                    line_dict['item_name']=get_value(item,'name')
                    line_dict['note']=get_value(item,'note')
                    line_dict['total_money']=item['total_money']['amount']/100
                    orders_format.append(line_dict) 


            orders_df = pd.DataFrame(orders_format)

            orders_df['customer_name']= orders_df['first_name'] + ' ' + orders_df['last_name']
            match_fees_export = orders_df[(orders_df['state'].isin(['COMPLETED','OPEN'])) & (orders_df['tenders'].notnull())][['id', 'created_at', 'variation_name','item_name', 'customer_name', 'total_money', 'note']]
            # match_fees_export = match_fees_export[match_fees_export['tenders'].notnull()]


            match_fees_export = match_fees_export[(match_fees_export['customer_name'].notnull()) | (match_fees_export['note'].notnull())]


            match_fees_export = match_fees_export[(match_fees_export['item_name'].fillna('').str.lower().str.contains('sub'))|(match_fees_export['item_name'].fillna('').str.lower().str.contains('training'))]

            match_fees_export.columns = exist.columns

            mg = pd.merge(left=match_fees_export, right=exist, how='left', on='ID', suffixes=['', '_old'])
            not_in = mg[mg['Date_old'].isnull()][exist.columns]
            # print(match_fees_export)
            not_in.fillna('NA', inplace=True)
            not_in.sort_values('Date', inplace=True)

            return not_in












        # Create a text element and let the reader know the data is loading.
        data_load_state = st.text('Loading Excel Sheet...')


        exist = google_sheet_func(SAMPLE_SPREADSHEET_ID_input, SAMPLE_RANGE_NAME)

        # Notify the reader that the data was successfully loaded.
        data_load_state.text("Google Sheet Loaded:")

        st.write(exist)


        subs_load_state = st.text('Getting Latest payments and details')

        dt = get_most_recent_sub_date(exist)
        payments = get_payments(dt, exist)

        subs_load_state.text(f'Payments Loaded:')

        st.subheader('Latest Payments:')
        st.write(payments)

        
        if st.button('Add to sheet'):
            append_to_sheet('Square Subs', SAMPLE_SPREADSHEET_ID_input, payments)
            st.text('Rows added to df')
        st.button('Reload page')

    elif option == 'Generate Match Invoices':
        st.text(option)
elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')


