#!/usr/bin/env python
# coding: utf-8
from datetime import datetime

# Create spark session and setting  spark naster session
from pyspark.sql import SparkSession

spark = SparkSession.builder.master('spark://spark:7077').appName("spark_alert").getOrCreate()

# Import needed spark  classes and functions
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, BooleanType, DoubleType, TimestampType
from pyspark.sql import functions as F
from pyspark.sql.window import Window

#
# This is a reference data about column names for log csv files
# col_names = ['error_code', 'error_message', 'severity', 'log_location', 'mode', 'model', 'graphics', 'session_id',
# 'sdkv', 'test_mode', 'flow_id', 'flow_type', 'sdk_date', 'publisher_id', 'game_id', 'bundle_id', 'appv',
# 'language', 'os', 'adv_id', 'gdpr', 'ccpa', 'country_code', 'date']
#


# Manually define schema for csv log files
schema = StructType([
    StructField("error_code", IntegerType(), True),
    StructField("error_message", StringType(), True),
    StructField("severity", StringType(), True),
    StructField("log_location", StringType(), True),
    StructField("mode", StringType(), True),
    StructField("model", StringType(), True),
    StructField("graphics", StringType(), True),
    StructField("session_id", StringType(), True),
    StructField("sdkv", StringType(), True),
    StructField("test_mode", BooleanType(), True),
    StructField("flow_id", StringType(), True),
    StructField("flow_type", StringType(), True),
    StructField("sdk_date", StringType(), True),
    StructField("publisher_id", StringType(), True),
    StructField("game_id", StringType(), True),
    StructField("bundle_id", StringType(), True),
    StructField("appv", StringType(), True),
    StructField("language", StringType(), True),
    StructField("os", StringType(), True),
    StructField("adv_id", StringType(), True),
    StructField("gdpr", BooleanType(), True),
    StructField("ccpa", BooleanType(), True),
    StructField("country_code", StringType(), True),
    StructField("unix_date", StringType(), True),
])


# Defining necessary functions for processing csv log file

def windows_specification_for_range(**specs):
    """
    :param:
      specs(dict) is a dictionary with follow fields:
       - part_by: partitionby column, can be a python list;
       - ord_by: orderby column, can be a python list;
       - start: a value of time column of current record in dataframe;
       - end: specific period time in seconds in past from the value of time column of current record in dataframe

    :return:
      This function returns a window specification with specified range between start and end time in seconds.
    """
    if specs['part_by'] is not None:
        return Window.partitionBy(specs['part_by']).orderBy(specs['ord_by']).rangeBetween(specs['start'], specs['end'])
    else:
        return Window.partitionBy().orderBy(specs['ord_by']).rangeBetween(specs['start'], specs['end'])


def error_dataframe_generation(**args):
    """
       :param:
         args(dict) is a dictionary with follow fields:
          - data_frame: the name of dataframe where errors are counted;
          - win_specs: window specification of  time period and columns over which errors are counted;
          - err_col_name: a name of new column where results of error counting are recorded; The name should describe error
                          like one_hour_bundle_error
          - col_list: a list of columns that will be included in a new dataset
          - err_threshold: a number above which error count should be selected for further processing (emailing etc)

       :return:
         This function returns a selected columns and new columns with counting errors over specific window conditions.
       """

    # Creating new column for error counting
    err_df = args['data_frame'].withColumn(args['err_col_name'],
                                           F.sum(F.when(F.col("severity") == "Error", 1).otherwise(0)).over(
                                               args['win_specs']))
    # Creating new data frame with column error counts
    err_df = err_df.select(args['col_list']).where(
        err_df[args['err_col_name']] > args['err_threshold']).dropDuplicates()
    return err_df


def write_log_csv(filename, dframe):
    """
          :param:
            filename(str):
             - the name of csv file where errors over specific period will be written;
               the file name should describe how errors were counted (exp: one_hour_bundle_error)
            dframe(object):
             - col_list: a list of columns that will be included in a new dataset
          :return:
            This function returns a selected columns and new columns with counting errors over specific window conditions.
          """
    # Creating current date in the correct format
    date = datetime.now().strftime("%Y_%m_%d_%H_%M")
    # Check if dataframe is not empty and then write csv file
    if not dframe.isEmpty():
        dframe.toPandas().to_csv(f"/opt/mnt/unprocessed_alert/{filename}_{date}.csv")
    return


# General data preparations
# Reading data csv log file
df = spark.read.option("encoding", "utf-8").option("multiline", True).option("quote", "\"").option(
    "escape", "\"").schema(schema).csv('hdfs://namenode:9000/spark_data/*.csv')

# Creating column unix stamp data time column by removing the part after period
df = df.withColumn('unix_date_split', F.split(df['unix_date'], '\.').getItem(0).cast('long'))

# Creating column date with date format form unix datetime stamp
df = df.withColumn('date', F.from_unixtime('unix_date', format='yyyy-MM-dd HH:mm:ss'))

#  Creating alerts
#  First Alert
#  This alert will count and record time when were more than 10 errors in one minutes using a sliding window

# Creating windows specification arguments
no_part_winspecs = {
    'part_by': None,
    'ord_by': ['unix_date_split'],
    'start': -59,
    'end': 0
}

# Creating windows specification
one_minute_error_specs = windows_specification_for_range(**no_part_winspecs)

# Creating arguments for new dataframe with error counting column
error_one_min_args = {
    "data_frame": df,
    'win_specs': one_minute_error_specs,
    'err_col_name': 'one_min_error',
    'col_list': ['date', 'one_min_error'],
    'err_threshold': 10

}

# Creating new dataframe with error counting column
one_min_error_df = error_dataframe_generation(**error_one_min_args)

# Writing the dataframe with error counting column to csv file
write_log_csv(error_one_min_args['err_col_name'], one_min_error_df)

# Second Alert
#  This alert will count and record  when were more than 10 errors in one hour by bundle_id using a sliding window

# Creating windows specification arguments
part_by_win_specs = {
    'part_by': ['bundle_id'],
    'ord_by': ['unix_date_split'],
    'start': -3599,
    'end': 0
}

# Creating windows specification
one_our_bundle_error = windows_specification_for_range(**part_by_win_specs)

# Creating arguments for new dataframe with error counting column
error_one_hour_bundle_args = {
    "data_frame": df,
    'win_specs': one_our_bundle_error,
    'err_col_name': 'one_hour_bundle_error',
    'col_list': ['bundle_id', 'date', 'one_hour_bundle_error'],
    'err_threshold': 10

}

# Creating new dataframe with error counting column
one_hour_bundle_error_df = error_dataframe_generation(**error_one_hour_bundle_args)

# Writing the dataframe with error counting column to csv file
write_log_csv(error_one_hour_bundle_args['err_col_name'], one_hour_bundle_error_df)
