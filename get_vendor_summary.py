# step-1 ( import all the modules)

import pandas as pd 
import sqlite3
import logging
from ingestion_db import ingest_db
import time 

logging.basicConfig(
    filename="logs/get_vendor_summary.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)


# step-2 (create the function to get the final table)


def create_vendor_summary(conn):
    start_creation=time.time()# to see the time 
    Vendor_summary=pd.read_sql_query("""
        with FreightSummary as (
            select
                VendorNumber,
                sum(Freight) as FreightCost
            from vendor_invoice
            group by VendorNumber
        ),

        PurchaseSummary as (
            select
                PUR.VendorNumber,
                PUR.VendorName,
                PUR.Brand,
                PUR.Description,
                PUR.PurchasePrice,
                PUR_P.Volume,
                PUR_P.Price as ActualPrice,
                sum(PUR.Quantity) AS TotalPurchaseQuantity,
                sum(PUR.Dollars) AS TotalPurchaseDollars
            from purchases as PUR
            join purchase_prices as PUR_P
                ON PUR.Brand = PUR_P.Brand
            where PUR.PurchasePrice > 0
            group by 
                PUR.VendorName,
                PUR.VendorNumber,
                PUR.Brand,
                PUR.Description,
                PUR.PurchasePrice,
                PUR_P.Price,
                PUR_P.Volume
        ),

        SalesSummary as (
            select
                VendorNo,
                Brand,
                sum(SalesDollars) as TotalSalesDollar,
                sum(SalesPrice) as TotalSalesPrice,
                sum(SalesQuantity) as TotalSalesQuantity,
                sum(ExciseTax) as TotalExciseTax
            from Sales
            group by VendorNo, Brand
        )

        SELECT 
            ps.VendorNumber,
            ps.VendorName,
            ps.Brand,
            ps.Description,
            ps.PurchasePrice,
            ps.ActualPrice,
            ps.Volume,
            ps.TotalPurchaseQuantity,
            ps.TotalPurchaseDollars,
            ss.TotalSalesQuantity,
            ss.TotalSalesDollar,
            ss.TotalSalesPrice,
            ss.TotalExciseTax,
            fs.FreightCost
        FROM PurchaseSummary AS ps
        LEFT JOIN SalesSummary AS ss
            ON ps.VendorNumber = ss.VendorNo
            AND ps.Brand = ss.Brand
        LEFT JOIN FreightSummary AS fs
            ON ps.VendorNumber = fs.VendorNumber
        ORDER BY ps.TotalPurchaseDollars DESC;
        """, conn)
    end_creation=time.time()
    time_taken_creation=end_creation-start_creation
    print('time taken for creation :',time_taken_creation)
    return Vendor_summary

# Step-3 (create a function to clean the data)

def clean_data(df):
    statr_cleaning=time.time()
    df['Volume']=df['Volume'].astype('float')#changing data type to float 

    df.fillna(0,inplace=True) # filling missing/null values with 0

    # removing extraa space from columns 
    df['VendorName']=df['VendorName'].str.strip()
    df['Description']=df['Description'].str.strip()


    #creating new columns for better analysis 
    df['GrossProfit']=df['TotalSalesDollar']-df['TotalPurchaseDollars']
    df['ProfitMargin']=(df['GrossProfit']/df['TotalSalesDollar'])*100
    df['StockTurnover']=df['TotalSalesQuantity']/df['TotalPurchaseQuantity']
    df['SalesToPurchaseRatio']=df['TotalSalesDollar']/df['TotalPurchaseDollars']

    end_cleaning=time.time()
    print(f'time_taken_for_cleaning: {end_cleaning-statr_cleaning}')
    return df

# Step-4 (now use the injestion_db sript to inser this data inside the database)

# now we will write our main function
if __name__=='__main__':
    # creating dtaabase connection 
    conn=sqlite3.connect('inventory.db')

    logging.info('creating vendor_summary table')
    summary_df=create_vendor_summary(conn) # this takes connection as a argument 
    logging.info(summary_df.head()) # in logs file this will show the top 5 data records of the table that is created 

    logging.info('cleaning the data')
    clean_df=clean_data(summary_df)
    logging.info(clean_df.head())

    logging.info('ingesting the data in database')
    ingest_db(clean_df,'vendor_sales_summary',conn) # this is the name of the function inside the ingestion_db file and these are the arguments it take 
    logging.info('completed')


