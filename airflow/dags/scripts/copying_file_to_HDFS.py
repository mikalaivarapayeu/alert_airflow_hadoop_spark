# Importing necessary libraries
from hdfs import InsecureClient


def copy_to_hdfs():
    """
        This function copy data.csv file to Hadoop distributed system.
        :param:
            None
        :return:
            None
        """
    # Creating hdfs client
    hdfs_client = InsecureClient('http://namenode:9870')
    # Defining location the file in local file system and destination location in HDFS
    local_file_path = '/opt/mnt/data/data.csv'
    hdfs_path = '/spark_data/data.csv'
    # Copying file for local file system to hdfs
    with open(local_file_path, 'rb') as local_file:
        hdfs_client.write(hdfs_path, local_file, overwrite=True)


if __name__ == '__main__':
    copy_to_hdfs()
