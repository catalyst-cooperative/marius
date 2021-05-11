import glob
import math
import os

import numpy as np
import pandas as pd
from pyspark.sql.window import Window
from pyspark.sql import SparkSession
from pyspark.sql.functions import rand, floor, lit, monotonically_increasing_id, row_number, col

SRC_COL = "src"
REL_COL = "rel"
DST_COL = "dst"
INDEX_COL = "index"
SRC_EDGE_BUCKET_COL = "src_part"
DST_EDGE_BUCKET_COL = "dst_part"
PARTITION_ID = "partition_id"
NODE_LABEL = "node_label"
RELATION_LABEL = "relation_label"
TMP_DATA_DIRECTORY = "tmp_pyspark"

COLUMN_SCHEMA = [SRC_COL, REL_COL, DST_COL]

SPARK_APP_NAME = "marius_preprocessor"


def remap_columns(df, has_rels):
    if not has_rels:
        df = df.withColumn(REL_COL, lit(0))
    return df.select(COLUMN_SCHEMA)


def convert_to_binary(input_filename, output_filename):
    assert (input_filename != output_filename)

    with open(output_filename, "wb") as output_file:
        for chunk in pd.read_csv(input_filename, header=None, chunksize=10 ** 7, sep="\t", dtype=int):
            chunk_array = chunk.to_numpy(dtype=np.int32)
            output_file.write(bytes(chunk_array))

    os.system("rm {}".format(input_filename))


def write_df_to_csv(df, output_filename):
    df.coalesce(1).write.csv(TMP_DATA_DIRECTORY, mode="overwrite", sep="\t")
    tmp_file = glob.glob("{}/*.csv".format(TMP_DATA_DIRECTORY))[0]
    os.system("mv {} {}".format(tmp_file, output_filename))
    os.system("rm -rf {}".format(TMP_DATA_DIRECTORY))


def write_partitioned_df_to_csv(partition_triples, num_partitions, output_filename):
    partition_triples.write.partitionBy(SRC_EDGE_BUCKET_COL, DST_EDGE_BUCKET_COL).csv(TMP_DATA_DIRECTORY,
                                                                                      mode="overwrite", sep="\t")

    partition_offsets = []
    with open(output_filename, "w") as output_file:
        for i in range(num_partitions):
            for j in range(num_partitions):
                tmp_file = glob.glob(
                    "{}/{}={}/{}={}/*.csv".format(TMP_DATA_DIRECTORY, SRC_EDGE_BUCKET_COL, str(i), DST_EDGE_BUCKET_COL,
                                                  str(j)))[0]
                pd.read_csv(tmp_file, sep="\t")
                with open(tmp_file, 'r') as g:
                    lines = g.readlines()
                    partition_offsets.append(len(lines))
                    output_file.writelines(lines)

    os.system("rm -rf {}".format(TMP_DATA_DIRECTORY))

    return partition_offsets


def assign_ids(df):
    return df.withColumn(INDEX_COL, row_number().over(Window.orderBy(monotonically_increasing_id())) - 1)


def remap_edges(edges_df, nodes, rels):
    remapped_edges_df = edges_df.join(nodes, edges_df.src == nodes.node_label) \
        .drop(NODE_LABEL, SRC_COL) \
        .withColumnRenamed(INDEX_COL, SRC_COL) \
        .join(rels, edges_df.rel == rels.relation_label) \
        .drop(RELATION_LABEL, REL_COL) \
        .withColumnRenamed(INDEX_COL, REL_COL) \
        .join(nodes, edges_df.dst == nodes.node_label) \
        .drop(NODE_LABEL, DST_COL) \
        .withColumnRenamed(INDEX_COL, DST_COL)

    return remapped_edges_df


def get_edge_buckets(edges_df, nodes_with_partitions, num_partitions):
    partition_triples = edges_df.join(nodes_with_partitions, edges_df.src == nodes_with_partitions.index) \
        .drop(NODE_LABEL, INDEX_COL) \
        .withColumnRenamed(PARTITION_ID, SRC_EDGE_BUCKET_COL) \
        .join(nodes_with_partitions, edges_df.dst == nodes_with_partitions.index) \
        .drop(NODE_LABEL, INDEX_COL) \
        .withColumnRenamed(PARTITION_ID, DST_EDGE_BUCKET_COL)
    partition_triples = partition_triples.repartition(num_partitions ** 2, SRC_EDGE_BUCKET_COL, DST_EDGE_BUCKET_COL)

    return partition_triples


def assign_partitions(nodes, num_partitions):
    partition_size = math.ceil(nodes.count() / num_partitions)
    nodes_with_partitions = nodes.withColumn(PARTITION_ID, floor(nodes.index / partition_size)).drop(NODE_LABEL)
    return nodes_with_partitions


def get_nodes_df(edges_df):
    nodes = edges_df.select(col(SRC_COL).alias(NODE_LABEL)).union(edges_df.select(col(DST_COL).alias(NODE_LABEL))) \
        .distinct().coalesce(1).orderBy(rand())
    nodes = assign_ids(nodes).cache()
    return nodes


def get_relations_df(edges_df):
    rels = edges_df.drop(SRC_COL, DST_COL).distinct().coalesce(1).orderBy(rand())\
        .withColumnRenamed(REL_COL, RELATION_LABEL)
    rels = assign_ids(rels).cache()
    return rels


def preprocess_dataset(edges_files, num_partitions, output_dir, splits=(.05, .05), columns=None, header=False,
                       header_length=0, delim="\t"):
    map_columns = False
    has_rels = True
    if columns is None:
        columns = COLUMN_SCHEMA
    else:
        map_columns = True
        if REL_COL not in columns:
            has_rels = False

    spark = SparkSession.builder.appName(SPARK_APP_NAME).config('spark.driver.memory', '8g').config(
        'spark.executor.memory', '1g').getOrCreate()

    all_edges_df = None
    train_edges_df = None
    valid_edges_df = None
    test_edges_df = None
    if len(edges_files) == 1:
        train_split = 1.0 - splits[0] - splits[1]
        valid_split = splits[0]
        test_split = splits[1]

        # read in the edge file
        all_edges_df = spark.read.option("header", header).option("comment", "#").csv(edges_files, sep=delim).toDF(
            *columns)

        if map_columns:
            all_edges_df = remap_columns(all_edges_df, has_rels)

        # split into train/valid/test tests
        train_edges_df, valid_edges_df, test_edges_df = all_edges_df.randomSplit([train_split, valid_split, test_split])

    elif len(edges_files) == 3:
        all_edges_df = spark.read.option("header", header).csv(edges_files, sep=delim).toDF(*columns)
        train_edges_df = spark.read.option("header", header).csv(edges_files[0], sep=delim).toDF(*columns)
        valid_edges_df = spark.read.option("header", header).csv(edges_files[1], sep=delim).toDF(*columns)
        test_edges_df = spark.read.option("header", header).csv(edges_files[2], sep=delim).toDF(*columns)

        if map_columns:
            all_edges_df = remap_columns(all_edges_df, has_rels)
            train_edges_df = remap_columns(train_edges_df, has_rels)
            valid_edges_df = remap_columns(valid_edges_df, has_rels)
            test_edges_df = remap_columns(test_edges_df, has_rels)
    else:
        print("Incorrect number of input files")
        exit(-1)

    # get node and relation labels and assign indices
    nodes = get_nodes_df(all_edges_df)
    rels = get_relations_df(all_edges_df)

    # replace node and relation labels with indices
    train_edges_df = remap_edges(train_edges_df, nodes, rels)
    valid_edges_df = remap_edges(valid_edges_df, nodes, rels)
    test_edges_df = remap_edges(test_edges_df, nodes, rels)

    # store mapping of labels to indices
    write_df_to_csv(nodes, output_dir + "node_mapping.txt")
    write_df_to_csv(rels, output_dir + "relation_mapping.txt")

    tmp_train_file = output_dir + "tmp_train_edges.txt"
    tmp_valid_file = output_dir + "tmp_valid_edges.txt"
    tmp_test_file = output_dir + "tmp_test_edges.txt"

    if num_partitions > 1:

        # assigns partition to each node
        nodes_with_partitions = assign_partitions(nodes, num_partitions)

        # creates edge buckets for the training set given the partitions for each node
        partition_triples = get_edge_buckets(train_edges_df, nodes_with_partitions, num_partitions)

        # writes edge buckets to a single csv file and returns offsets to the edge buckets in that file
        partition_offsets = write_partitioned_df_to_csv(partition_triples, num_partitions, tmp_train_file)

        with open(output_dir + "train_edges_partitions.txt", "w") as g:
            g.writelines([str(o) + "\n" for o in partition_offsets])
    else:
        write_df_to_csv(train_edges_df, tmp_train_file)

    # write valid/test sets to single csv
    write_df_to_csv(valid_edges_df, tmp_valid_file)
    write_df_to_csv(test_edges_df, tmp_test_file)

    # convert csv files to binary output required by Marius
    convert_to_binary(tmp_train_file, output_dir + "train_edges.pt")
    convert_to_binary(tmp_valid_file, output_dir + "valid_edges.pt")
    convert_to_binary(tmp_test_file, output_dir + "test_edges.pt")