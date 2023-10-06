import streamlit as st
import pandas as pd
import numpy as np
from google_sheets import *
import streamlit_authenticator as stauth
from PIL import Image

from boto import get_square_secret
from square.client import Client
import os
import yaml
from yaml.loader import SafeLoader

import uuid
import datetime as dt



col4, col5, col6 = st.columns(3, gap='small')

image=Image.open("logo.png")


with col4:    
    st.image(
                "https://oldthorntoniansfc.com/wp-content/uploads/2021/02/Old-Thorntonians-Crest-2014_150dpi.png",
                width=100, # Manually Adjust the width of the image as per requirement
            )
with col5: 
    st.image(
                image,
                width=300, # Manually Adjust the width of the image as per requirement
            )
with col6:
    st.write('')



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
        ('Get New Payments', 'Generate Match Invoices', 'Generate Training Invoices'))


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
            
            s_orders = orders_api.search_orders(body)
            
            if s_orders.is_success():
                if len(s_orders.body)>0:
                    s_orders=s_orders.body['orders']

                


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
                        if 'invoices' in result.body.keys():
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


                    match_fees_export = match_fees_export[(match_fees_export['item_name'].fillna('').str.lower().str.contains('sub'))|(match_fees_export['item_name'].fillna('').str.lower().str.contains('training'))|(match_fees_export['item_name'].fillna('').str.lower().str.contains('card'))]

                    match_fees_export.columns = exist.columns

                    mg = pd.merge(left=match_fees_export, right=exist, how='left', on='ID', suffixes=['', '_old'])
                    not_in = mg[mg['Date_old'].isnull()][exist.columns]
                    # print(match_fees_export)
                    not_in.fillna('NA', inplace=True)
                    not_in.sort_values('Date', inplace=True)

                    return not_in
                else:
                    return pd.DataFrame()
            else:
                return pd.DatFrame()












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

        SAMPLE_SPREADSHEET_ID_input = '1lalOwWx_GwUZgjG3WgyxZvirtT9GYDJ6t3dAuNimTLM'
        SAMPLE_RANGE_NAME = 'OTPI Scores!A:V'

        data_load_state = st.text('Loading Match History...')


        opti_scores = get_spread_sheet(SAMPLE_SPREADSHEET_ID_input, SAMPLE_RANGE_NAME)

        # Notify the reader that the data was successfully loaded.
        data_load_state.text("Match History Loaded:")

        match_weeks = ['-------']+list(opti_scores['Game Date'].drop_duplicates())

        match_week = st.selectbox(
            'Select Match Week:',
            match_weeks)

        if match_week!= '-------':
            match_week_games = opti_scores[opti_scores['Game Date']==match_week]
            teams = list(match_week_games['OT Team'].sort_values().drop_duplicates())

            invoice_teams = st.multiselect(
                'What teams do you want to generate invoices for:',
                teams,
                teams)
            
            invoices_to_raise = match_week_games[match_week_games['OT Team'].isin(invoice_teams)]


            debt_state = st.text('Getting Current Debt...')
            SAMPLE_SPREADSHEET_ID_input = '1K_uXqI1eiguBMr0uH3Tu7xDzePAIi3uAsDrAWukyBq8'
            SAMPLE_RANGE_NAME = 'Overall Summary!B2:D1000'

            matchday_debt = get_spread_sheet(SAMPLE_SPREADSHEET_ID_input, SAMPLE_RANGE_NAME)
            matchday_debt = matchday_debt[matchday_debt['Name']!='']

            

            invoice_mg_1 = pd.merge(left=invoices_to_raise, right = matchday_debt, how = 'left', right_on='Name', left_on = 'Player Name')
            invoice_mg_1['Match Day Debt'] = pd.to_numeric(invoice_mg_1['Match Day Debt'].str.replace('£', ''))
            invoice_mg = invoice_mg_1[invoice_mg_1['Match Day Debt']>0]
            invoice_mg['Amount Owed']=pd.to_numeric(invoice_mg['Amount Owed'])
            invoice_mg = invoice_mg[invoice_mg['Amount Owed']>0]
            #
            invoice_mg=invoice_mg[['Player Name', 'OT Team', 'Game Date', 'Opposition Name', 'Amount Owed']]

            debt_state.text('Invoices to raise:')

            st.write(invoice_mg)

            create_invoices = st.button('Create Invoices')

            if create_invoices:
                client = Client(
                access_token=get_square_secret()['SQUARE_ACCESS_TOKEN'],
                environment='production')

                customers_api = client.customers

                invoice_status = st.text('Getting Customer Info...')
                result = customers_api.list_customers(
    
                )
                customers = {str(cust.get('given_name')) + ' ' + str(cust.get('family_name')):cust.get('id') for cust in result.body['customers']}


                i=1
                while result.cursor:
                    # print(i)
                    i+=1
                    result = customers_api.list_customers(
                        cursor = result.cursor
                    )
                    customers2 = {str(cust.get('given_name')) + ' ' + str(cust.get('family_name')):cust.get('id') for cust in result.body['customers']}

                    customers.update(customers2)
                
                customer_df=pd.DataFrame(data=[{'name':cust, 'id':customers[cust]} for cust in customers])

                invoice_mg['match_inv_id']=range(0,len(invoice_mg))

                id_mg = pd.merge(left = invoice_mg, right = customer_df, how= 'left', left_on = 'Player Name', right_on = 'name')

                


                invoice_status.text('Creating Orders...')

                orders_api = client.orders

                new_orders = []

                for i, row in id_mg.iterrows():
                    print(i)
                    amount = row['Amount Owed'] 
                    body = {
                        'order': {
                            'location_id': 'SBBJSGR24YHYB',
                            'reference_id': f'{uuid.uuid1()}',
                            'line_items': [
                                
                                {
                                    'quantity': '1',
                                    'catalog_object_id': 'OKAX666RRB7XKNM6BJTRM6IM',
                                    'base_price_money': {
                                        'amount': amount*100,
                                        'currency': 'GBP'
                                    }
                                }
                            ]
                        },
                        'idempotency_key': f'{uuid.uuid1()}'
                    }
                    # print(body)
                    
                    result = orders_api.create_order(body)
                    # print(result)
                    obj_id=result.body['order']['id']

                    new_orders.append({'Player Name':row['Player Name'], 'match_inv_id':row['match_inv_id'], 'obj_id':obj_id})
                # st.write(pd.DataFrame(new_orders))
                # st.write(id_mg)
                order_mg= pd.merge(left = id_mg, right=pd.DataFrame(new_orders), how= 'left', on = ['Player Name', 'match_inv_id'])

                invoice_status.text('Creating Invoices...')

                invoices_api = client.invoices

                invoices = []
                to_create=order_mg[order_mg['id'].notnull()]
                skipped=order_mg[order_mg['id'].isnull()]
                for i, row in to_create.iterrows():
                    order_id = row['obj_id']
                    cust_id = row['id']
                    invoice_number = str(dt.datetime.now().date()) +f"_{row['OT Team']}"+f"_{row['obj_id']}_1"

                    due_at =  str(dt.datetime.now().date() + dt.timedelta(days = 1))

                    title = 'Match Subs ' + row['Game Date'] + ' vs ' + row['Opposition Name']

                        
                    body = {
                    'invoice': {
                        'location_id': 'SBBJSGR24YHYB',
                        'order_id': f'{order_id}',
                        'primary_recipient': {
                            'customer_id': f'{cust_id}'
                        },
                        'payment_requests': [
                            {
                                'request_type': 'BALANCE',
                                'due_date': due_at,
                                'tipping_enabled': True,
                                'automatic_payment_source': 'NONE',
                                'reminders': [
                                    {
                                        'relative_scheduled_days': -1,
                                        'message': 'Your Invoice is due'
                                    }
                                ]
                            }
                        ],
                        'delivery_method': 'EMAIL',
                        'invoice_number': invoice_number,
                        'title': title,
                        'description': title,
                        'scheduled_at': due_at+'T10:00:00Z',
                        'accepted_payment_methods': {
                            'card': True,
                            'square_gift_card': False,
                            'bank_account': False,
                            'buy_now_pay_later': False,
                            'cash_app_pay': False
                        },
                        'sale_or_service_date': str(dt.datetime.now().date()),
                        'store_payment_method_enabled': False
                    },
                    'idempotency_key': f'{uuid.uuid1()}'
                    }

                    result = invoices_api.create_invoice(body)
                    # print(result)
                    invidid=result.body['invoice']['id']
                    invoices.append(invidid)


                invoice_status.text('Publishing Invoices...')
                results = []
                for invidid in invoices:

                    body = {
                        'version': 0,
                        'idempotency_key': f'{invidid}'
                    }

                    result = invoices_api.publish_invoice(
                        invidid,
                        body
                    )
                    results.append(result)

                invoice_status.text('Publishing Created...')
                st.write(results)

                st.write('No Customer Details so Skipped:')
                st.write(skipped)
    
    elif option == 'Generate Training Invoices':
        def getColumnName(n):
 
            # initialize output string as empty
            result = ''
        
            while n > 0:
        
                # find the index of the next letter and concatenate the letter
                # to the solution
        
                # here index 0 corresponds to 'A', and 25 corresponds to 'Z'
                index = (n - 1) % 26
                result += chr(index + ord('A'))
                n = (n - 1) // 26
        
            return result[::-1]
        
        st.write(option)

        SAMPLE_SPREADSHEET_ID_input = '1hDe02yfWW59_6xlVRt4DyN20dgBuMa5fipD_DDsgHeA'
        SAMPLE_RANGE_NAME = 'Summary!A6:FM6'

              
        data_load_state = st.text('Getting training dates...')


        exist = get_spread_sheet(SAMPLE_SPREADSHEET_ID_input, SAMPLE_RANGE_NAME)  
        training_dates=['-------']+[x for x in list(exist.columns) if x!='']
        # Notify the reader that the data was successfully loaded.
        data_load_state.text("Dates Loaded:")

        training_date = st.selectbox(
        'Select Training Date:',
        training_dates)

        if training_date!= '-------':

            owed_state = st.text('Calculating Owed...')

            index=training_dates.index(training_date)-1
            col_number=(index*4)+3
            col = getColumnName(col_number)

            attended_range = f'Summary!{col}7:{col}'

            attended = get_spread_sheet(SAMPLE_SPREADSHEET_ID_input, attended_range)

            player_range = f'Summary!B8:B'

            players = get_spread_sheet(SAMPLE_SPREADSHEET_ID_input, player_range)

            header=list(players.columns)[0]

            players_ls=[header]+list(players[header])
            attended_filt=attended[attended.index<len(players_ls)].copy()
            attended_filt['Players']=players_ls

            owed_state.text('Calculating Debt...')

            SAMPLE_SPREADSHEET_ID_input = '1K_uXqI1eiguBMr0uH3Tu7xDzePAIi3uAsDrAWukyBq8'
            SAMPLE_RANGE_NAME = 'Overall Summary!B2:F1000'

            training_debt = get_spread_sheet(SAMPLE_SPREADSHEET_ID_input, SAMPLE_RANGE_NAME)
            training_debt = training_debt[training_debt['Name']!='']

            invoice_mg_1 = pd.merge(left=attended_filt, right = training_debt, how = 'left', right_on='Name', left_on = 'Players')
            invoice_mg_1['Training Debt'] = pd.to_numeric(invoice_mg_1['Training Debt'].str.replace('£', ''))
            invoice_mg_1['Owed'] = pd.to_numeric(invoice_mg_1['Owed'].str.replace('£', '').str.replace('-', '0'))

            
            invoice_mg = invoice_mg_1[invoice_mg_1['Owed']>0]
            invoice_mg = invoice_mg[invoice_mg['Training Debt']>0]
            owed_state.text('Players to Invoice...')

            invoice_mg=invoice_mg[['Name', 'Owed']]
            st.write(invoice_mg)
            create_invoices = st.button('Create Invoices')

            if create_invoices:
                invoice_status = st.write('Create Invoices')

                
                client = Client(
                access_token=get_square_secret()['SQUARE_ACCESS_TOKEN'],
                environment='production')

                customers_api = client.customers

                invoice_status = st.text('Getting Customer Info...')
                result = customers_api.list_customers(
    
                )
                customers = {str(cust.get('given_name')) + ' ' + str(cust.get('family_name')):cust.get('id') for cust in result.body['customers']}


                i=1
                while result.cursor:
                    # print(i)
                    i+=1
                    result = customers_api.list_customers(
                        cursor = result.cursor
                    )
                    customers2 = {str(cust.get('given_name')) + ' ' + str(cust.get('family_name')):cust.get('id') for cust in result.body['customers']}

                    customers.update(customers2)
                
                customer_df=pd.DataFrame(data=[{'name':cust, 'id':customers[cust]} for cust in customers])

                invoice_mg['match_inv_id']=range(0,len(invoice_mg))

                id_mg = pd.merge(left = invoice_mg, right = customer_df, how= 'left', left_on = 'Name', right_on = 'name')

                st.write(id_mg)

                invoice_status.text('Creating Orders...')

                orders_api = client.orders

                new_orders = []

                for i, row in id_mg.iterrows():
                    print(i)
                    amount = row['Owed'] 
                    body = {
                        'order': {
                            'location_id': 'SBBJSGR24YHYB',
                            'reference_id': f'{uuid.uuid1()}',
                            'line_items': [
                                
                                {
                                    'quantity': '1',
                                    'catalog_object_id': 'FLDAWYXJJW5L5NGKQFLVU3NC',
                                    'base_price_money': {
                                        'amount': amount*100,
                                        'currency': 'GBP'
                                    }
                                }
                            ]
                        },
                        'idempotency_key': f'{uuid.uuid1()}'
                    }
                    # print(body)
                    
                    result = orders_api.create_order(body)
                    # print(result)
                    obj_id=result.body['order']['id']

                    new_orders.append({'Name':row['Name'], 'match_inv_id':row['match_inv_id'], 'obj_id':obj_id})
                # st.write(pd.DataFrame(new_orders))
                # st.write(id_mg)
                order_mg= pd.merge(left = id_mg, right=pd.DataFrame(new_orders), how= 'left', on = ['Name', 'match_inv_id'])
                st.write(order_mg)

                invoice_status.text('Creating Invoices...')

                invoices_api = client.invoices

                invoices = []
                to_create=order_mg[order_mg['id'].notnull()]
                skipped=order_mg[order_mg['id'].isnull()]
                for i, row in to_create.iterrows():
                    order_id = row['obj_id']
                    cust_id = row['id']
                    invoice_number = str(dt.datetime.now().date()) +f"_{training_date}"+f"_{row['obj_id']}_1"

                    due_at =  str(dt.datetime.now().date() + dt.timedelta(days = 1))

                    title = 'Training Subs ' + training_date

                        
                    body = {
                    'invoice': {
                        'location_id': 'SBBJSGR24YHYB',
                        'order_id': f'{order_id}',
                        'primary_recipient': {
                            'customer_id': f'{cust_id}'
                        },
                        'payment_requests': [
                            {
                                'request_type': 'BALANCE',
                                'due_date': due_at,
                                'tipping_enabled': True,
                                'automatic_payment_source': 'NONE',
                                'reminders': [
                                    {
                                        'relative_scheduled_days': -1,
                                        'message': 'Your Invoice is due'
                                    }
                                ]
                            }
                        ],
                        'delivery_method': 'EMAIL',
                        'invoice_number': invoice_number,
                        'title': title,
                        'description': title,
                        'scheduled_at': due_at+'T10:00:00Z',
                        'accepted_payment_methods': {
                            'card': True,
                            'square_gift_card': False,
                            'bank_account': False,
                            'buy_now_pay_later': False,
                            'cash_app_pay': False
                        },
                        'sale_or_service_date': str(dt.datetime.now().date()),
                        'store_payment_method_enabled': False
                    },
                    'idempotency_key': f'{uuid.uuid1()}'
                    }

                    result = invoices_api.create_invoice(body)
                    # print(result)
                    invidid=result.body['invoice']['id']
                    invoices.append(invidid)


                invoice_status.text('Publishing Invoices...')
                results = []
                for invidid in invoices:

                    body = {
                        'version': 0,
                        'idempotency_key': f'{invidid}'
                    }

                    result = invoices_api.publish_invoice(
                        invidid,
                        body
                    )
                    results.append(result)

                invoice_status.text('Publishing Created...')
                st.write(results)

                st.write('No Customer Details so Skipped:')
                st.write(skipped)

        
elif authentication_status == False:
    st.error('Username/password is incorrect')
elif authentication_status == None:
    st.warning('Please enter your username and password')


# 4BRM4M7P7YC3HOP65FIZHYK5
