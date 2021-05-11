#!/usr/bin/env bash

BASE_DIR=freebase_16
NUM_PART=16

CMD="python osdi2021/pbg_preprocessing/parquet_to_hdf5.py --edge_dir_in "$BASE_DIR/train" --ent_part_count $NUM_PART --entity_dir "$BASE_DIR/entities" --relation_dir "$BASE_DIR/relations" --edge_dir_out "$BASE_DIR/freebase_train" --output_path "$BASE_DIR/freebase_metadata""
$CMD

CMD="python osdi2021/pbg_preprocessing/parquet_to_hdf5.py --edge_dir_in "$BASE_DIR/valid" --ent_part_count $NUM_PART --entity_dir None --relation_dir None --edge_dir_out "$BASE_DIR/freebase_valid" --output_path None"
$CMD

CMD="python osdi2021/pbg_preprocessing/parquet_to_hdf5.py --edge_dir_in "$BASE_DIR/test" --ent_part_count $NUM_PART --entity_dir None --relation_dir None --edge_dir_out "$BASE_DIR/freebase_test" --output_path None"
$CMD