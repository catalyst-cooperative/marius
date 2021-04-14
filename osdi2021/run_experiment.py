import argparse
import os
import sys
from os import path
import execute as e
import json
from buffer_simulator import plotting as plot_buff
import plotting as osdi_plot

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))) + "/tools")
import tools.preprocess as preprocess


def run_marius(config, exp_dir, name, config_args="", overwrite=False):
    e.cleanup_experiments()
    if not os.path.exists(exp_dir + name + "_result.json") or overwrite:
        print("==== Running Marius: %s =====" % name)
        dstat_pid, nvidia_smi_pid = e.start_tracing()
        e.run_marius(config, config_args)
        e.stop_metric_collection(dstat_pid, nvidia_smi_pid)
        info_log, dstat_df, nvidia_smi_df = e.collect_metrics()
        e.cleanup_experiments()

        with open(exp_dir + name + "_result.json", 'w') as out_file:
            json.dump(info_log, out_file)
            print("Marius output results written to: %s" % exp_dir + name + "_result.json")
        with open(exp_dir + name + "_dstat.csv", 'w') as out_file:
            dstat_df.to_csv(out_file)
            print("Dstat tracing results written to: %s" % exp_dir + name + "_dstat.csv")
        with open(exp_dir + name + "_nvidia_smi.csv", 'w') as out_file:
            nvidia_smi_df.to_csv(out_file)
            print("Nvidia-smi tracing results written to: %s" % exp_dir + name + "_nvidia_smi.csv")
    else:
        print("Marius: %s already run" % name)


def run_pbg(runner_file, config, exp_dir, name, overwrite=False):
    e.cleanup_experiments()
    if not os.path.exists(exp_dir + name + "_result.json") or overwrite:
        print("==== Running PBG: %s =====" % name)
        dstat_pid, nvidia_smi_pid = e.start_tracing()
        e.run_pbg(runner_file, config)
        e.stop_metric_collection(dstat_pid, nvidia_smi_pid)
        info_log, dstat_df, nvidia_smi_df = e.collect_metrics(pbg=True)
        e.cleanup_experiments()

        with open(exp_dir + name + "_result.json", 'w') as out_file:
            json.dump(info_log, out_file)
            print("PBG output results written to: %s" % exp_dir + name + "_result.json")
        with open(exp_dir + name + "_dstat.csv", 'w') as out_file:
            dstat_df.to_csv(out_file)
            print("Dstat tracing results written to: %s" % exp_dir + name + "_dstat.csv")
        with open(exp_dir + name + "_nvidia_smi.csv", 'w') as out_file:
            nvidia_smi_df.to_csv(out_file)
            print("Nvidia-smi tracing results written to: %s" % exp_dir + name + "_nvidia_smi.csv")
    else:
        print("PBG: %s already run" % name)


def run_dglke(cmd, exp_dir, name, overwrite=False):
    e.cleanup_experiments()
    if not os.path.exists(exp_dir + name + "_result.json") or overwrite:
        print("==== Running DGL-KE: %s =====" % name)
        dstat_pid, nvidia_smi_pid = e.start_tracing()
        e.run_dglke(cmd)
        e.stop_metric_collection(dstat_pid, nvidia_smi_pid)
        info_log, dstat_df, nvidia_smi_df = e.collect_metrics(dglke=True)
        e.cleanup_experiments()

        with open(exp_dir + name + "_result.json", 'w') as out_file:
            json.dump(info_log, out_file)
            print("DGL-KE output results written to: %s" % exp_dir + name + "_result.json")
        with open(exp_dir + name + "_dstat.csv", 'w') as out_file:
            dstat_df.to_csv(out_file)
            print("Dstat tracing results written to: %s" % exp_dir + name + "_dstat.csv")
        with open(exp_dir + name + "_nvidia_smi.csv", 'w') as out_file:
            nvidia_smi_df.to_csv(out_file)
            print("Nvidia-smi tracing results written to: %s" % exp_dir + name + "_nvidia_smi.csv")
    else:
        print("DGL-KE: %s already run" % name)


def run_fb15k(overwrite=False):
    exp_dir = "osdi2021/system_comparisons/fb15k/marius/"

    distmult_config = exp_dir + "distmult.ini"
    complex_config = exp_dir + "complex.ini"

    if not os.path.exists("fb15k/"):
        print("==== Preprocessing FB15K =====")
        preprocess.fb15k("fb15k/")

    run_marius(distmult_config, exp_dir, "distmult_fb15k", overwrite=overwrite)
    run_marius(complex_config, exp_dir, "complex_fb15k", overwrite=overwrite)

    exp_dir = "osdi2021/system_comparisons/fb15k/dgl-ke/"
    with open(exp_dir + "complex.txt", "r") as f:
        dglke_complex_cmd = f.readlines()[0]
    with open(exp_dir + "distmult.txt", "r") as f:
        dglke_distmult_cmd = f.readlines()[0]

    run_dglke(dglke_complex_cmd, exp_dir, "complex_fb15k", overwrite=overwrite)
    run_dglke(dglke_distmult_cmd, exp_dir, "distmult_fb15k", overwrite=overwrite)

    # PBG may throw errors
    exp_dir = "osdi2021/system_comparisons/fb15k/pbg/"

    runner_file = exp_dir + "run_fb15k.py"
    complex_config = exp_dir + "fb15k_complex_config.py"
    distmult_config = exp_dir + "fb15k_distmult_config.py"
    run_pbg(runner_file, complex_config, exp_dir, "complex_fb15k", overwrite=overwrite)
    run_pbg(runner_file, distmult_config, exp_dir, "distmult_fb15k", overwrite=overwrite)

    osdi_plot.print_table_2()


def run_livejournal(overwrite=False):
    exp_dir = "osdi2021/system_comparisons/livejournal/marius/"
    dot_config = exp_dir + "dot.ini"

    if not os.path.exists("livejournal/"):
        print("==== Preprocessing Livejournal =====")
        preprocess.live_journal("livejournal/")

    run_marius(dot_config, exp_dir, "dot_livejournal", overwrite=overwrite)

    # PBG may throw errors
    exp_dir = "osdi2021/system_comparisons/livejournal/pbg/"

    runner_file = exp_dir + "run_dot.py"
    dot_config = exp_dir + "dot.py"
    run_pbg(runner_file, dot_config, exp_dir, "dot_livejournal", overwrite=overwrite)

    osdi_plot.print_table_3()


def run_twitter(overwrite=False):
    exp_dir = "osdi2021/system_comparisons/twitter/marius/"

    dot_config = exp_dir + "dot.ini"

    if not os.path.exists("twitter/"):
        print("==== Preprocessing Twitter =====")
        preprocess.twitter("twitter/")

    run_marius(dot_config, exp_dir, "dot_twitter", overwrite=overwrite)

    osdi_plot.print_table_4()


def run_freebase86m(overwrite=False):
    exp_dir = "osdi2021/system_comparisons/freebase86m/marius/"
    complex_config = exp_dir + "d100.ini"

    if not os.path.exists("freebase86m_p16/"):
        print("==== Preprocessing Freebase86m P=16 D=100 =====")
        preprocess.freebase86m("freebase86m_p16/", num_partitions=16)

    run_marius(complex_config, exp_dir, "freebase86m_16", overwrite=overwrite)

    osdi_plot.print_table_5()


def run_utilization(overwrite=False):
    exp_dir = "osdi2021/system_comparisons/freebase86m/marius/"

    complex_50_config = exp_dir + "d50.ini"
    complex_50_8_config = exp_dir + "d50_8.ini"

    if not os.path.exists("freebase86m/"):
        print("==== Preprocessing Freebase86m P=1 D=50 =====")
        preprocess.freebase86m("freebase86m/")

    config_args = "--training.num_epochs=1 --evaluation.epochs_per_eval=2"
    run_marius(complex_50_config, exp_dir, "complex_50_util", config_args, overwrite=overwrite)

    if not os.path.exists("freebase86m_p8/"):
        print("==== Preprocessing Freebase86m P=8 D=50 =====")
        preprocess.freebase86m("freebase86m_p8/", num_partitions=8)

    run_marius(complex_50_8_config, exp_dir, "complex_50_8_util", config_args, overwrite=overwrite)

    exp_dir = "osdi2021/system_comparisons/freebase86m/dgl-ke/"
    with open(exp_dir + "complex.txt", "r") as f:
        dglke_complex_cmd = f.readlines()[0]

    try:
        run_dglke(dglke_complex_cmd, exp_dir, "complex_50_util", overwrite=overwrite)
    except Exception as e:
        print(e)


def run_buffer_simulator(overwrite=False):
    exp_dir = "osdi2021/buffer_simulator/"

    n_start = 8
    c_start = 2
    num = 5
    total_size = 86E6 * 4 * 2 * 100 # total embedding size for freebase86m d=100
    plot_buff.plot_varying_num_partitions_io(n_start, c_start, num, total_size, exp_dir + "figure7.png")
    print("Figure written to %s" % exp_dir + "figure7.png")


def run_orderings_total_io(overwrite=False):
    exp_dir = "osdi2021/partition_orderings/freebase86m/"

    elimination_config = exp_dir + "elimination.ini"
    hilbert_config = exp_dir + "hilbert.ini"
    hilbert_symmetric_config = exp_dir + "hilbert_symmetric.ini"

    if not os.path.exists("freebase86m_32/"):
        print("==== Preprocessing Freebase86m P=32 D=100 =====")
        preprocess.freebase86m("freebase86m_32/", num_partitions=32)

    config_args = "--training.num_epochs=1 --evaluation.epochs_per_eval=2 --reporting.logs_per_epoch=1000"
    run_marius(elimination_config, exp_dir, "elimination100_util", config_args, overwrite=overwrite)

    run_marius(hilbert_config, exp_dir, "hilbert100_util", config_args, overwrite=overwrite)

    run_marius(hilbert_symmetric_config, exp_dir, "hilbertsymmetric100_util", config_args, overwrite=overwrite)


def run_orderings_freebase86m(overwrite=False):
    exp_dir = "osdi2021/partition_orderings/freebase86m/"

    elimination_config = exp_dir + "elimination.ini"
    hilbert_config = exp_dir + "hilbert.ini"
    hilbert_symmetric_config = exp_dir + "hilbert_symmetric.ini"
    memory_config = exp_dir + "memory.ini"

    if not os.path.exists("freebase86m_32/"):
        print("==== Preprocessing Freebase86m P=32 D=100 =====")
        preprocess.freebase86m("freebase86m_32/", num_partitions=32)

    run_marius(elimination_config, exp_dir, "elimination100", overwrite=overwrite)
    run_marius(hilbert_config, exp_dir, "hilbert100", overwrite=overwrite)
    run_marius(hilbert_symmetric_config, exp_dir, "hilbertsymmetric100", overwrite=overwrite)

    if not os.path.exists("freebase86m/"):
        print("==== Preprocessing Freebase86m P=1 D=50 =====")
        preprocess.freebase86m("freebase86m/")

    config_args = "--model.embedding_size=50"
    run_marius(elimination_config, exp_dir, "elimination50", overwrite=overwrite)
    run_marius(hilbert_config, exp_dir, "hilbert50", config_args, overwrite=overwrite)
    run_marius(hilbert_symmetric_config, exp_dir, "hilbertsymmetric50", config_args, overwrite=overwrite)
    run_marius(memory_config, exp_dir, "memory50", config_args, overwrite=overwrite)


def run_orderings_twitter(overwrite=False):
    exp_dir = "osdi2021/partition_orderings/twitter/"

    elimination_config = exp_dir + "elimination.ini"
    hilbert_config = exp_dir + "hilbert.ini"
    hilbert_symmetric_config = exp_dir + "hilbert_symmetric.ini"
    memory_config = exp_dir + "memory.ini"

    if not os.path.exists("twitter_32/"):
        print("==== Preprocessing Twitter P=32 D=200 =====")
        preprocess.freebase86m("twitter_32/", num_partitions=32)

    if not os.path.exists("twitter/"):
        print("==== Preprocessing Twitter P=1 D=100 =====")
        preprocess.freebase86m("twitter/")

    run_marius(elimination_config, exp_dir, "elimination100", overwrite=overwrite)
    run_marius(hilbert_config, exp_dir, "hilbert100", overwrite=overwrite)
    run_marius(hilbert_symmetric_config, exp_dir, "hilbertsymmetric100", overwrite=overwrite)
    run_marius(memory_config, exp_dir, "memory100", overwrite=overwrite)

    config_args = "--model.embedding_size=200"
    run_marius(elimination_config, exp_dir, "elimination200", config_args, overwrite=overwrite)
    run_marius(hilbert_config, exp_dir, "hilbert200", config_args, overwrite=overwrite)
    run_marius(hilbert_symmetric_config, exp_dir, "hilbertsymmetric200", config_args, overwrite=overwrite)


def run_staleness_bound(overwrite=False):
    exp_dir = "osdi2021/microbenchmarks/bounded_staleness/"

    all_async_config = exp_dir + "all_async.ini"
    all_sync = exp_dir + "all_sync.ini"
    sync_relations_async_nodes = exp_dir + "sync_relations_async_nodes.ini"

    if not os.path.exists("freebase86m/"):
        print("==== Preprocessing Freebase86m P=1 D=50 =====")
        preprocess.freebase86m("freebase86m/")

    run_marius(all_sync, exp_dir, "all_sync", overwrite=overwrite)

    for bound in [2, 4, 8, 16, 32, 64]:
        config_args = "--training_pipeline.max_batches_in_flight=%i" % bound
        run_marius(all_async_config, exp_dir, "all_async_%i" % bound, config_args, overwrite=overwrite)
        run_marius(sync_relations_async_nodes, exp_dir, "sync_rel_%i" % bound, config_args, overwrite=overwrite)


def run_prefetching(overwrite=False):
    exp_dir = "osdi2021/microbenchmarks/prefetching/"

    no_prefetching_config = exp_dir + "no_prefetching.ini"
    prefetching_config = exp_dir + "prefetching.ini"

    if not os.path.exists("freebase86m_32/"):
        print("==== Preprocessing Freebase86m P=32 D=100 =====")
        preprocess.freebase86m("freebase86m_32/", num_partitions=32)

    run_marius(no_prefetching_config, exp_dir, "no_prefetching", overwrite=overwrite)
    run_marius(prefetching_config, exp_dir, "prefetching", overwrite=overwrite)


def run_big_embeddings(overwrite=False):
    exp_dir = "osdi2021/large_embeddings/"
    cpu_memory = exp_dir + "cpu_memory.ini"
    gpu_memory = exp_dir + "gpu_memory.ini"
    disk = exp_dir + "disk.ini"
    if not os.path.exists("freebase86m/"):
        print("==== Preprocessing Freebase86m P=1 =====")
        preprocess.freebase86m("freebase86m/")

    if not os.path.exists("freebase86m_32/"):
        print("==== Preprocessing Freebase86m P=32 =====")
        preprocess.freebase86m("freebase86m_32/", num_partitions=32)

    run_marius(gpu_memory, exp_dir, "d20", overwrite=overwrite)
    run_marius(cpu_memory, exp_dir, "d50", overwrite=overwrite)

    config_args = "--storage.buffer_capacity=16"
    run_marius(disk, exp_dir, "d100", config_args, overwrite=overwrite)

    osdi_plot.print_table_6()

    # config_args = "--storage.buffer_capacity=4 --model.embedding_size=400"
    # run_marius(disk, exp_dir, "d400", config_args)
    #
    # if not os.path.exists("freebase86m_64/"):
    #     print("==== Preprocessing Freebase86m P=64 =====")
    #     preprocess.freebase86m("freebase86m_64/", num_partitions=64)

    # config_args = "--storage.buffer_capacity=4 --model.embedding_size=800"
    # run_marius(disk, exp_dir, "d800", config_args)


def run_all():
    experiment_dict = {
        "fb15k": run_fb15k,
        "livejournal": run_livejournal,
        "twitter": run_twitter,
        "freebase86m": run_freebase86m,
        "utilization": run_utilization,
        "buffer_simulator": run_buffer_simulator,
        "orderings_total_io": run_orderings_total_io,
        "orderings_freebase86m": run_orderings_freebase86m,
        "orderings_twitter": run_orderings_twitter,
        "staleness_bound": run_staleness_bound,
        "prefetching": run_prefetching,
        "big_embeddings": run_big_embeddings
    }

    print("#### Running all experiments ####\n")
    for k, v in experiment_dict.items():
        print("#### Running %s ####\n" %k)
        try:
            v()
            print("#### %s Complete ####\n" %k)
        except Exception as e:
            print(e)
            print("#### %s Failed ####\n" %k)


if __name__ == "__main__":
    experiment_dict = {
        "fb15k": run_fb15k,
        "livejournal": run_livejournal,
        "twitter": run_twitter,
        "freebase86m": run_freebase86m,
        "utilization": run_utilization,
        "buffer_simulator": run_buffer_simulator,
        "orderings_total_io": run_orderings_total_io,
        "orderings_freebase86m": run_orderings_freebase86m,
        "orderings_twitter": run_orderings_twitter,
        "staleness_bound": run_staleness_bound,
        "prefetching": run_prefetching,
        "big_embeddings": run_big_embeddings,
        "all": run_all
    }
    parser = argparse.ArgumentParser(description='Reproduce experiments ')
    parser.add_argument('--experiment', metavar='experiment', type=str, choices=experiment_dict.keys(),
                        help='Experiment choices: %(choices)s')
    parser.add_argument('--overwrite', metavar='overwrite', action='store_true',
                        help='If true, the results of previously run experiments will be overwritten.')

    args = parser.parse_args()
    experiment_dict.get(args.experiment)(args.overwrite)