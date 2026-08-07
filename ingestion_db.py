import pandas as pd 
import os 
import sqlite3
import logging 
import time 

logging.basicConfig(
    filename="logs/ingestion_db.log",
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filemode='a'
)



# to check whether the os is able to load the directories in data folder 
# for file in os.listdir('DATA'):
#     print(file)

# seetting up sqlite3 connection 
conn=sqlite3.connect("inventory.db")


# MAKING AN INGEST FUNCTION 
def ingest_db(df,table_name,connection):
    df.to_sql(table_name,con=connection,if_exists='replace',index=False,chunksize=100000)

# when your data is continuously comming from any seerver and continuously you have to store that into your database so for that you should have to do scripting, that means when the data arrives it will automatically stored into the database and also you have to schedule that script accordingly 

# now to load the files data into dataframe 
def load_raw_data():# this function will load the csv as dataframe and ingest them into db 
    start=time.time() # to get the start time of ingestion 
    for file in os.listdir("DATA"):
        df=pd.read_csv('DATA/'+file)
        logging.info(f'ingesting{file} in db') # this df.shape will check whether the file is added to dataframe or not 
        ingest_db(df,file[:-4],conn)
    end=time.time() # to get the end time of ingestion
    total_time=(end-start)/60 # because it will give us time in seconds so divided by 60 
    logging.info('Ingestion complete')
    logging.info(f'total time taken {total_time} in minutes')


if __name__=='__main__':
    load_raw_data()

