# %%
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import pandas as pd
from square.client import Client

# %%
scopes = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

# %%
SAMPLE_SPREADSHEET_ID_input = '1K_uXqI1eiguBMr0uH3Tu7xDzePAIi3uAsDrAWukyBq8'
SAMPLE_RANGE_NAME = 'Square Subs!A:G'

# %%

creds = ServiceAccountCredentials.from_json_keyfile_name("googlecreds.json", scopes)


# %%
client = gspread.authorize(creds)

# %%
sheet = client.open_by_key("1h5hBte_aDD9FwTDoTN1ymSh-LNIBe2wyq1QrQYhSwNE")


# %%
match_worksheet = sheet.worksheet('Match Subs')


# Print the DataFrame to verify

# Define the range of data you want (e.g., "A1:D10")
cell_range = match_worksheet.get('A1:I')

# Convert the cell range to a DataFrame
df = pd.DataFrame(cell_range[1:], columns=cell_range[0])  # First row as header




# %%
train_worksheet = sheet.worksheet('Training Subs')



# Print the DataFrame to verify

# Define the range of data you want (e.g., "A1:D10")
cell_range = train_worksheet.get('A1:F')

# Convert the cell range to a DataFrame
df_train = pd.DataFrame(cell_range[1:], columns=cell_range[0])  # First row as header




# %%
df_train

# %%
square_subs = df[df['Channel']=='Square'].copy()
square_subs['Date']=pd.to_datetime(square_subs['Date'])


train_subs = df_train[df_train['Time']!='']
train_subs['Date']=pd.to_datetime(train_subs['Date']).copy()
train_subs

# %%
maxd=min(square_subs['Date'].max(), train_subs['Date'].max())
maxds=maxd.strftime("%Y-%m-%dT00:00:00.000Z")
maxds

# %%
client = Client(
    access_token= 'EAAAFO_dqOOnvRZCLDvOtKfBGznlxPy5zb4anviDPIJBjXjXGkmo5d6w1jxoxtCn',#get_square_secret()['SQUARE_ACCESS_TOKEN'],
    environment='production')


# %%
orders_api = client.orders
customers_api = client.customers

# %%
body = {
    'location_ids': [
        'SBBJSGR24YHYB'
    ],
    'query': {
        'filter': {
            
            'date_time_filter': {
                'created_at': {
                    'start_at': f'{maxds}',
                    "end_at": "2025-01-21T15:12:20.000Z",
                }
            },
      # "state_filter": {
        # "states": [
        #   "COMPLETED"
        # ]
      # }
       },
    "sort": {
      "sort_field": "UPDATED_AT",
      "sort_order": "DESC"
    }
        
    },
   }

# %%
result = orders_api.search_orders(body)
s_orders = result.body['orders']


i=1
while result.cursor:
    print(i)
    i+=1
    result = orders_api.search_orders(body,
        cursor = result.cursor
    )
    s_orders.append(result.body['orders'])

    # customers.update(customers2)

# %%
for x in s_orders:
    try:
        a = x['line_items']
    except:
        print(x)

# %%
invoices_api = client.invoices


result = invoices_api.list_invoices(
    'SBBJSGR24YHYB'
)

invoices = pd.DataFrame(result.body['invoices'])

i=1
while result.cursor:
    print(i)
    i+=1
    result = invoices_api.list_invoices(
        'SBBJSGR24YHYB',
        cursor = result.cursor
    )
    print(result.cursor)
invoices = pd.concat([invoices, pd.DataFrame(result.body['invoices'])])
invoices


# %%
def get_value(key1,key2):
    try:
        return key1[key2] 
    except:
        return None

# %%
orders_format = []
for i, order in enumerate(s_orders[:]):
    
    print(i, '/', len(s_orders))
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

    if 'line_items' in order: 
        for item in order['line_items']:
            line_dict = new_order.copy()
            
            line_dict['variation_name']=get_value(item,'variation_name')
            line_dict['item_name']=get_value(item,'name')

            # if 'raining' in line_dict['item_name']:
            #     print(item)
            line_dict['note']=get_value(item,'note')
            line_dict['total_money']=item['total_money']['amount']/100
            orders_format.append(line_dict) 


orders_df = pd.DataFrame(orders_format)

# %%
orders_df[['variation_name', 'item_name']].drop_duplicates()

# %%
match_square = orders_df[orders_df['item_name'].str.lower().str.contains('match')]
match_square=match_square[match_square['first_name'].notnull()]
match_square['Transaction ID']=match_square['id']
match_square

# %%
train_square = orders_df[orders_df['item_name'].str.lower().str.contains('raining')]
train_square=train_square[train_square['first_name'].notnull()]
train_square['Transaction ID']=train_square['id']
train_square

# %%
trans = df[['Transaction ID']].drop_duplicates()
trans=trans[trans['Transaction ID']!='']
trans['FLAG']=1
trans

# %%
match_mg = pd.merge(left=match_square,right=trans, how='left', on=['Transaction ID'])
match_to_upload=match_mg[match_mg['FLAG']!=1].copy()
match_to_upload

# %%
df_train

# %%
trans = df_train[['Transaction ID']].drop_duplicates()
trans=trans[trans['Transaction ID']!='']
trans['FLAG']=1
trans

# %%
train_mg = pd.merge(left=train_square,right=trans, how='left', on=['Transaction ID'])
train_to_upload=train_mg[train_mg['FLAG']!=1].copy()
train_to_upload

# %%
match_to_upload['Date']=match_to_upload['created_at'].apply(lambda x: x[:10])
match_to_upload['Time']=match_to_upload['created_at'].apply(lambda x: x[11:19])
match_to_upload['Net Sales']=match_to_upload['total_money']
match_to_upload['Customer Name']=match_to_upload['first_name'] + ' ' + match_to_upload['last_name']
match_to_upload['Description']='Match Sub (Full Game) - TEst'
match_to_upload['Payment ID']=''
match_to_upload['Channel']='Square'
match_to_upload_final = match_to_upload[['Date', 'Time', 'Net Sales', 'Transaction ID', 'Payment ID', 'Customer Name', 'Description', 'Channel']]
match_to_upload_final
                                                            
                                                        
                                            

# %%
train_to_upload['Date']=train_to_upload['created_at'].apply(lambda x: x[:10])
train_to_upload['Time']=train_to_upload['created_at'].apply(lambda x: x[11:19])
train_to_upload['Gross Sales']=train_to_upload['total_money']
train_to_upload['Customer Name']=train_to_upload['first_name'] + ' ' + train_to_upload['last_name']
# match_to_upload['Description']='Match Sub (Full Game) - TEst'
# match_to_upload['Payment ID']=''
# match_to_upload['Channel']='Square'
train_to_upload_final = train_to_upload[['Date', 'Time', 'Gross Sales', 'Customer Name', 'Gross Sales', 'Transaction ID']]
                                                            
                                                        
train_to_upload_final

# %%
import datetime as dt
def date_to_serial(date):
    epoch = dt.datetime(1899, 12, 30)
    return (date - epoch).days + (date - epoch).seconds / 86400  # Include fraction for time if necessary

# Apply the date serial conversion for the 'Join Date' column
train_to_upload_final['Date']=pd.to_datetime(train_to_upload_final['Date'])
train_to_upload_final['Date'] = train_to_upload_final['Date'].apply(date_to_serial)
match_to_upload_final['Date']=pd.to_datetime(match_to_upload_final['Date'])
match_to_upload_final['Date'] = match_to_upload_final['Date'].apply(date_to_serial)

# %%
data_list = match_to_upload_final.values.tolist()
data_list



last_row = len(match_worksheet.get_all_values()) 
next_row = last_row + 1  # Start appending after the last row

# # Prepare the range where you want to update (adjust the column range as needed)
cell_range = f'A{next_row}:I{next_row + len(data_list) - 1}'

# # Update the range with the data
match_worksheet.update(cell_range, data_list, value_input_option='RAW')

# %%
data_list = train_to_upload_final.values.tolist()
data_list



last_row = len(train_worksheet.get_all_values()) 
next_row = last_row + 1  # Start appending after the last row

# # Prepare the range where you want to update (adjust the column range as needed)
cell_range = f'A{next_row}:F{next_row + len(data_list) - 1}'

# # Update the range with the data
train_worksheet.update(cell_range, data_list, value_input_option='RAW')

# %%



