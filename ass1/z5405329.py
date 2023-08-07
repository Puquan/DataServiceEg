# Student Name: Puquan Chen
# Student ID: z5405329

import json
import matplotlib.pyplot as plt
import pandas as pd
import sys
import os
import numpy as np
import math
import re

studentid = os.path.basename(sys.modules[__name__].__file__)


def log(question, output_df, other):
    print("--------------- {}----------------".format(question))

    if other is not None:
        print(question, other)
    if output_df is not None:
        df = output_df.head(5).copy(True)
        for c in df.columns:
            df[c] = df[c].apply(lambda a: a[:20] if isinstance(a, str) else a)

        df.columns = [a[:10] + "..." for a in df.columns]
        print(df.to_string())
        

def find_foreignPortCountry(df1): # for Q4
    country = {}
    groupby_df = df1.groupby('Country')
    for groupName, df in groupby_df:
        for i in df['ForeignPort']:
            country[i] = groupName
            
    
    return country


def find_CountryRegion(df): # for Q7
    region = {}
    groupby_df = df.groupby('Port_Region')
    for regionName, dataframe in groupby_df:
        for i in dataframe['Port_Country']:
            region[i] = regionName
    region['Hong Kong'] = 'NE Asia'
    return region

def preprocess_df1(df1, df2): # for Q7
    df1 = df1[49668:].reset_index(drop=True) # September 2003 to September 2022
    region_dict = find_CountryRegion(df2)
    n = 0
    for i in df1['Country']:
        if i in region_dict.keys():
            region = region_dict[i]
            df1.loc[n, "Port_Region"] = region
            n += 1
        else:
            df1.loc[n, "Port_Region"] = "Unknown"
            n += 1
    return df1



def question_1(city_pairs):
    """
    :return: df1
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """

    df1 = pd.read_csv(city_pairs)
    
    n = 0
    for i, j in zip(df1["Passengers_In"], df1['Passengers_Out']):
        if i > j:
            df1.loc[n, "passenger_in_out"] = "IN"
        elif i < j:
            df1.loc[n, "passenger_in_out"] = "OUT" 
        else:
            df1.loc[n, 'passenger_in_out'] = "SAME"
        n += 1
    
    n = 0 
    for i, j in zip(df1["Freight_In_(tonnes)"], df1['Freight_Out_(tonnes)']):
        if i > j:
            df1.loc[n, "freight_in_out"] = "IN" 
        elif i < j: 
            df1.loc[n, "freight_in_out"] = "OUT"
        else:
            df1.loc[n, "freight_in_out"] = "SAME"
        n += 1
        
    n = 0 
    for i, j in zip(df1["Mail_In_(tonnes)"], df1['Mail_Out_(tonnes)']):
        if i > j:
            df1.loc[n, "mail_in_out"] = "IN"
        elif i < j:
            df1.loc[n, "mail_in_out"] = "OUT" 
        else:
            df1.loc[n, "mail_in_out"] = "SAME"
        n += 1
        
    
    
    

    log("QUESTION 1", output_df=df1[["AustralianPort", "ForeignPort", "passenger_in_out", "freight_in_out", "mail_in_out"]], other=df1.shape)
    return df1


def question_2(df1):
    """
    :param df1: the dataframe created in question 1
    :return: dataframe df2
            Please read the assignment specs to know how to create the output dataframe
    """

    record = []
    portNames = set(df1["AustralianPort"])
    for portName in portNames:
        temp = df1.loc[df1['AustralianPort']==portName]
        count_passengerIn = len(temp[temp['passenger_in_out']=='IN'])
        count_passengerOut = len(temp[temp['passenger_in_out']=='OUT'])
        count_freightIn= len(temp[temp['freight_in_out']=='IN'])
        count_freightOut = len(temp[temp['freight_in_out']=='OUT'])
        count_mailIn = len(temp[temp['mail_in_out']=='IN'])
        count_mailOut = len(temp[temp['mail_in_out']=='OUT'])
        port_list = [portName,count_passengerIn, count_passengerOut, count_freightIn, count_freightOut, count_mailIn,count_mailOut]
        record.append(port_list)
    temp_df2 = pd.DataFrame(record, columns =['AustralianPort', 'PassengerInCount', 'PassengerOutCount', 'FreightInCount', 'FreightOutCount', 'MailInCount', 'MailOutCount'])
    df2 = temp_df2.sort_values(by='PassengerInCount', ascending=False).reset_index(drop=True)

    log("QUESTION 2", output_df=df2, other=df2.shape)
    return df2


def question_3(df1):
    """
    :param df1: the dataframe created in question 1
    :return: df3
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """
    record = []
    groupby_df = df1.groupby('Country')
    
    
    for groupName, df in groupby_df:
        average_passengerIn = df['Passengers_In'].mean().round(2)
        average_passengerOut = df['Passengers_Out'].mean().round(2)

        average_freightIn= df['Freight_In_(tonnes)'].mean().round(2)
        average_freightOut = df['Freight_Out_(tonnes)'].mean().round(2)

        average_mailIn = df['Mail_In_(tonnes)'].mean().round(2)
        average_mailOut = df['Mail_Out_(tonnes)'].mean().round(2)
    
    
    
    
        counrty_list = [groupName,average_passengerIn, average_passengerOut, average_freightIn, average_freightOut, average_mailIn, average_mailOut]
        record.append(counrty_list)

    
    temp_df3 = pd.DataFrame(record, columns =['Country', 'Passengers_in_average', 'Passengers_out_average', 'Freight_in_average', 'Freight_out_average', 'Mail_in_average', 'Mail_out_average'])
    df3 = temp_df3.sort_values(by='Passengers_in_average', ascending=True).reset_index(drop=True)

    log("QUESTION 3", output_df=df3, other=df3.shape)
    return df3


def question_4(df1):
    """
    :param df1: the dataframe created in question 1
    :return: df4
            Data Type: Dataframe
            Please read the assignment specs to know how to create the output dataframe
    """

    country_list = set(df1["Country"])
    country_dict = {key: 0 for key in country_list}
    
    countryPort_pairs = find_foreignPortCountry(df1)
    

    temp_df = df1.loc[df1['Passengers_Out'] > 0] # passengers_out > 0

    groupby_df = temp_df.groupby(['Month','AustralianPort'])
    
    for groupName, df in groupby_df:
        AustralianPort = groupName[1]
        for i in df['ForeignPort']:
            country = countryPort_pairs[i]
            country_dict[country] += 1
            
    df4 = pd.DataFrame(country_dict.items(), columns=["Country", "Unique_ForeignPort_Count"]).sort_values(
    by=["Unique_ForeignPort_Count","Country"], ascending=False, ignore_index=True).head()
    

    log("QUESTION 4", output_df=df4, other=df4.shape)
    return df4


def question_5(seats):
    """
    :param seats : the path to dataset
    :return: df5
            Data Type: dataframe
            Please read the assignment specs to know how to create the  output dataframe
    """
    df5 = pd.read_csv(seats)
    n = 0
    for i, j, k in zip(df5["In_Out"], df5['Australian_City'], df5['International_City']):
        if i == 'I':
            df5.loc[n, "Source_City"] = k
            df5.loc[n, "Destination_City"] = j
        elif i == 'O':
            df5.loc[n, "Source_City"] = j
            df5.loc[n, "Destination_City"] = k
            
        n += 1
    
    

    log("QUESTION 5", output_df=df5, other=df5.shape)
    return df5


def question_6(df5):
    """
    :param df5: the dataframe created in question 5
    :return: df6
    """
    
    groupby_df1 = df5.groupby(["Australian_City","International_City","Year","Airline"])
    average_maxSeat = []
    average_flight = []
    for groupName, df in groupby_df1:
        
        average_maxSeat.append([(groupName[0],groupName[1],groupName[2]),groupName[3],df['Max_Seats'].mean().round(2)])
    
        average_flight.append([(groupName[0],groupName[1],groupName[2]),groupName[3],df['All_Flights'].mean().round(2)])
    
    groupby_df2 = df5.groupby(["Australian_City","International_City","Year"])
    
    
    sum_maxSeat = {}

    for groupName, df in groupby_df2:
        australianCity = groupName[0]
        internationalCity = groupName[1]
        year_sum =  df['Max_Seats'].sum()
        sum_maxSeat[groupName] = year_sum
        
        
    final = []
    for i in range(len(average_maxSeat)):
        australianCity = average_maxSeat[i][0][0]
        internationalCity = average_maxSeat[i][0][1]
        year = average_maxSeat[i][0][2]
        airline_company = average_maxSeat[i][1]

        current_averageMaxSeat = average_maxSeat[i][2]
        current_averageFlight = average_flight[i][2]

        if sum_maxSeat[average_maxSeat[i][0]] != 0:
            current_MarketShare = (current_averageMaxSeat / sum_maxSeat[average_maxSeat[i][0]]).round(2)
        else:
            current_MarketShare = 0

        final.append([year,airline_company,australianCity,internationalCity,current_averageFlight,current_averageMaxSeat,current_MarketShare])
    
    df6 = pd.DataFrame(final, columns =['Year', 'Airline', 'Australian_City', 'International_City', 'Average_Flight', 'Average_Maxseats', 'MarketShare'])
    

    log("QUESTION 6", output_df=df6, other=df6.shape)
    return df6

    """
    comments:
    Firstly, to analyse competing airlines, I group the data by airlines, australian cities and international cities to see how do they operate flight between different city pairs.
    Secondly, it is easier to analyse the trend by anual data instead of month. Therefore, I also group the data by year, then caculate the month average max_seat and flight from different airlines in a seperate year. 
    Thirdly, it is significant that to get the market share so that we can know what is rivals doing and know which rival is the most strongest, so that we can gain more advantage to take remaining market. Therefore, I calculate aunal market share for each airline for a specific route by "No. of Max_seat of Specific Airline route a year / Sum of the Max_seat from all airlines a year in a route".  
    To sum up, from this dataframe, you can get not only specific number data of a flight route to know the performance of a single airline, but also get the ratio of the market share of each airlines to analyse the correlation.
    """



def question_7(seats, city_pairs):
    """
    :param seats: the path to dataset
    :param city_pairs : the path to dataset
    :return: nothing, but saves the figure on the disk
    """
    
    df1 = question_1(city_pairs)
    df2 = question_5(seats)
    
    df1 = preprocess_df1(df1,df2)
    
    
    groupby_df1 = df1.groupby(['Year','Port_Region'])
    
    
    passenger_out = []
    passenger_in = []
    
    for groupName, df in groupby_df1:
        if groupName[1] == 'Unknown':
            continue
        if df.Passengers_Out.sum() != 0:
            passenger_out.append([groupName[0],groupName[1],df.Passengers_Out.sum()])
        if df.Passengers_In.sum() != 0:
            passenger_in.append([groupName[0],groupName[1],df.Passengers_In.sum()])
    
    group_df2 = df2.groupby(['Year','Port_Region','In_Out'])
    maxSeat_in = []
    maxSeat_out = []
    for groupName, df in group_df2:
        if groupName[2] == 'I' :
            maxSeat_in.append([groupName[0],groupName[1],df.Max_Seats.sum()])
        else:
            maxSeat_out.append([groupName[0],groupName[1],df.Max_Seats.sum()])
    
    out_percentage = {}
    in_percentage = {}
    
    
    
    for i in range(len(maxSeat_in)):
        year_out = maxSeat_out[i][0]
        region_out = maxSeat_out[i][1]
        percentage_out = passenger_out[i][2] / maxSeat_out[i][2]
        if region_out not in out_percentage.keys():
            out_percentage[region_out] = [percentage_out]
            
        else:
            out_percentage[region_out].append(percentage_out)
            
        
    
    
        year_in = maxSeat_in[i][0]
        region_in = maxSeat_in[i][1]
        percentage_in = passenger_in[i][2] / maxSeat_in[i][2]

        if region_in not in in_percentage.keys():
            in_percentage[region_in] = [percentage_in]
            
        else:
            in_percentage[region_in].append(percentage_in)
            
    out_percentage['S Asia'].insert(0, 0)
    in_percentage['S Asia'].insert(0, 0)
    out_percentage['Africa'].insert(-1, 0)
    in_percentage['Africa'].insert(-1, 0)
    
    
    
    fig = plt.figure(figsize=(9,9))
    plt.subplot(2, 1, 1,)
    # draw lines
    for label, values in in_percentage.items():
        # years for x
        x = range(int(2003), int(2023))
        y = values
        plt.plot(x, y, label=label, linewidth=1, linestyle='dashed')
    
    # legend and labels
    plt.legend(loc='upper right',ncol=2)
    plt.xlabel('Year')
    plt.ylabel('Passenger Seat Ratio')
    plt.xticks([2003,2008,2013,2018,2022])
    plt.title('Seat utilisation / Overseas to Australia')

    plt.subplot(2, 1, 2)
    for label, values in out_percentage.items():
        x = range(int(2003), int(2023))
        y = values
        plt.plot(x, y, label=label,linewidth=1,linestyle='dashed')
    
    plt.legend(loc='upper right',ncol=3)
    plt.xlabel('Year')
    plt.ylabel('Passenger Seat Ratio')
    plt.xticks([2003,2008,2013,2018,2022])
    plt.title('Seat Utilisation Rate/ Australia to Overseas')

    plt.subplots_adjust(left=0.1,
                        bottom=0.1,
                        right=0.9,
                        top=0.9,
                        wspace=0.4,
                        hspace=0.4)
    
            
    plt.savefig("{}-Q7.png".format(studentid))
    
    """
    Comments:
    Firstly, I think the statistics should be divided into two parts:
    1. Flights from Australia to Overseas
    2. Flights from Overseas to Australia
    since it is obvious that they are different in terms of travelling, bussiness, destination and so on, they should be analysed seperately.
    Secondly, the statistics should focus on the seat utilization rate along with time so that airlines can understand the performance of a certain flight according to the trend then optimise it. Therefore, I choose to draw line graphs, representing the relationship between time and seat utilization rate.
    Thirdly, I sort fights according to their corresponding service regions, because this is a better way to understand the tread around the world, by comparing different regions. The Airline can switch flights from low seat utilization rate region to high seat utilization rate region. To go more deeper, I may try to sort flights by flight companies after I sort them by regions so that airlines can understand what rivals do in diffenret regions.
    """
    

if __name__ == "__main__":
    df1 = question_1("city_pairs.csv")
    df2 = question_2(df1.copy(True))
    df3 = question_3(df1.copy(True))
    df4 = question_4(df1.copy(True))
    df5 = question_5("seats.csv")
    df6 = question_6(df5.copy(True))
    question_7("seats.csv", "city_pairs.csv")
