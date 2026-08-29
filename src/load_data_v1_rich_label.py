import scipy.io as io
import os
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TaskProgressColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
import numpy as np
import pickle
import argparse
import time
import pandas as pd


def normalize_sentence(text):
    """标准化句子文本，用于与标签文件匹配（小写、合并空白）。"""
    return ' '.join(str(text).lower().split())


def load_sentiment_labels(labels_file):
    """加载 task1-SR 情感标签 CSV（分号分隔，含注释行）。

    返回 {标准化句子文本: sentiment_label} 映射，label 取值为 -1/0/1（负/中/正）。
    文件不存在时返回 None。
    """
    if not os.path.exists(labels_file):
        return None
    df = pd.read_csv(labels_file, sep=';', comment='#', quotechar='"')
    label_map = {}
    for _, row in df.iterrows():
        label = row['sentiment_label']
        if pd.isna(label):
            # 含分号的句子被双引号包裹且没有 control 字段，标签被挤到 control 列
            label = row['control']
        if pd.isna(label):
            continue
        label_map[normalize_sentence(row['sentence'])] = float(label)
    return label_map


def ZuCo_data_v1(data_dir, save_data_dir, labels_file=None):

    console = Console()

    # 情感标签映射（仅 task1-SR 使用）。默认从 data_dir 同级目录找官方 sentiment_labels_task1.csv
    if labels_file is None:
        labels_file = os.path.join(os.path.dirname(data_dir), 'sentiment_labels_task1.csv')
    sentiment_labels = load_sentiment_labels(labels_file)
    if sentiment_labels is None:
        console.print(f'[yellow]提示：未找到情感标签文件 {labels_file}，将跳过 sentiment_label 映射（仅影响 task1-SR）[/yellow]')
    else:
        console.print(f'[green]已加载情感标签：{len(sentiment_labels)} 句（来自 {labels_file}）[/green]')

    EEG_data = os.path.join(save_data_dir, 'EEG_data', 'ZuCo1.0')
    os.makedirs(EEG_data, exist_ok=True)

    # Loop over the three tasks
    tasks = ['task1-SR', 'task2-NR', 'task3-TSR']

    for task in tasks:
        # 主任务不用进度条，直接打印任务名称（打印时没有活动的进度条重绘，避免错位）
        console.print(f'\n[bold cyan]{task}[/bold cyan]')

        input_mat_files_dir = os.path.join(data_dir, task, 'Matlab files')
        mat_files = os.listdir(input_mat_files_dir)
        path_mat_files = [os.path.join(input_mat_files_dir, mat_file) for mat_file in mat_files]
        dataset_dict = {} # 存储每个主体的句子数据
        n_sent_labeled = 0  # 统计成功映射到情感标签的句子数（仅 task1-SR）
        
        for mat_file in path_mat_files:
            # get subject id from the file name
            subject_name = os.path.basename(mat_file).split('.')[0].replace('results', '').strip()
            dataset_dict[subject_name] = []

            mat_data = io.loadmat(mat_file, squeeze_me=True, struct_as_record=False)['sentenceData']
            mat_data = np.atleast_1d(mat_data) # 转换为列表，方便遍历

            with Progress(
                SpinnerColumn(), # 加载动画
                TextColumn("[progress.description]{task.description}"), # 任务描述
                BarColumn(), # 进度条
                TaskProgressColumn(), # 任务百分比
                MofNCompleteColumn(), # 已完成进度数
                TimeRemainingColumn(), # 剩余时间
                TimeElapsedColumn(), # 已用时间
            ) as progress:
                task_id = progress.add_task("[red]" + subject_name, total = len(mat_data))
                # Sentence level data
                for sent_idx, sent in enumerate(mat_data):

                    word_data = sent.word # ndarray
                    # 判断当前句子的单词是否有效
                    if isinstance(word_data, np.ndarray):

                        # First key: sentence content
                        sent_obj = {'content': sent.content}

                        # 情感标签（仅 task1-SR 有，来自官方 sentiment_labels_task1.csv，-1/0/1 = 负/中/正）
                        if task == 'task1-SR' and sentiment_labels is not None:
                            sent_obj['sentiment_label'] = sentiment_labels.get(normalize_sentence(sent.content))
                            if sent_obj['sentiment_label'] is not None:
                                n_sent_labeled += 1

                        # 添加句子级原始 EEG 信号
                        sent_obj['rawData'] = sent.rawData  # ndarray (105, 4212)

                        # 存储句子水平的 EEG 特征（8 个频带均值，按频带分组）
                        sent_obj['sentence_level_EEG'] = {
                            'mean_t1': sent.mean_t1,   # theta 频带均值 1
                            'mean_t2': sent.mean_t2,   # theta 频带均值 2
                            'mean_a1': sent.mean_a1,   # alpha 频带均值 1
                            'mean_a2': sent.mean_a2,   # alpha 频带均值 2
                            'mean_b1': sent.mean_b1,   # beta 频带均值 1
                            'mean_b2': sent.mean_b2,   # beta 频带均值 2
                            'mean_g1': sent.mean_g1,   # gamma 频带均值 1
                            'mean_g2': sent.mean_g2    # gamma 频带均值 2
                        }

                        if task == 'task1-SR':
                            # task1-SR: Read sentences, answer control questions
                            sent_obj['answer_EEG'] = {
                                'answer_mean_t1': sent.answer_mean_t1,
                                'answer_mean_t2': sent.answer_mean_t2,
                                'answer_mean_a1': sent.answer_mean_a1,
                                'answer_mean_a2': sent.answer_mean_a2,
                                'answer_mean_b1': sent.answer_mean_b1,
                                'answer_mean_b2': sent.answer_mean_b2,
                                'answer_mean_g1': sent.answer_mean_g1,
                                'answer_mean_g2': sent.answer_mean_g2
                            }

                        # world level data
                        sent_obj['word'] = []

                        # Features from eye-tracking
                        word_tokens_has_fixation = []
                        word_tokens_all = []
                        word_tokens_with_mask = []

                        for word in word_data:
                            # 无论是否有注视，都计入全部词 token
                            word_tokens_all.append(word.content)

                            # 如果这个词有注视，才处理
                            if isinstance(word.nFixations, (int, np.integer)) and word.nFixations > 0:

                                word_obj = {'content': word.content, 'nFixations': word.nFixations}
                                word_obj['word_level_EEG'] = {}
                                word_obj['word_level_EEG']['FFD'] = {
                                    'FFD_t1': word.FFD_t1, 'FFD_t2': word.FFD_t2,
                                    'FFD_a1': word.FFD_a1, 'FFD_a2': word.FFD_a2,
                                    'FFD_b1': word.FFD_b1, 'FFD_b2': word.FFD_b2,
                                    'FFD_g1': word.FFD_g1, 'FFD_g2': word.FFD_g2
                                }

                                word_obj['word_level_EEG']['TRT'] = {
                                    'TRT_t1': word.TRT_t1, 'TRT_t2': word.TRT_t2,
                                    'TRT_a1': word.TRT_a1, 'TRT_a2': word.TRT_a2,
                                    'TRT_b1': word.TRT_b1, 'TRT_b2': word.TRT_b2,
                                    'TRT_g1': word.TRT_g1, 'TRT_g2': word.TRT_g2
                                }

                                word_obj['word_level_EEG']['GD'] = {
                                    'GD_t1': word.GD_t1, 'GD_t2': word.GD_t2,
                                    'GD_a1': word.GD_a1, 'GD_a2': word.GD_a2,
                                    'GD_b1': word.GD_b1, 'GD_b2': word.GD_b2,
                                    'GD_g1': word.GD_g1, 'GD_g2': word.GD_g2
                                }
                                
                                sent_obj['word'].append(word_obj)
                                word_tokens_has_fixation.append(word.content)
                                word_tokens_with_mask.append(word.content)

                            else:
                                # 如果这个词没有fixation，用MASK代替
                                word_tokens_with_mask.append('[MASK]')

                        sent_obj['word_tokens_has_fixation'] = word_tokens_has_fixation
                        sent_obj['word_tokens_with_mask'] = word_tokens_with_mask
                        sent_obj['word_tokens_all'] = word_tokens_all

                        dataset_dict[subject_name].append(sent_obj)
                    else:
                        print(sent_idx, type(word_data))

                    time.sleep(0.001)
                    progress.advance(task_id, advance = 1)

     

        # save the dataset_dict for each task
        output_file = f'{task}_v1.pkl'
        with open(os.path.join(EEG_data, output_file), 'wb') as handle:
            pickle.dump(dataset_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)

        # 打印标签映射统计（仅 task1-SR 有意义）
        if task == 'task1-SR':
            total_sents = sum(len(sents) for sents in dataset_dict.values())
            console.print(f'[dim]sentiment_label 已映射 {n_sent_labeled}/{total_sents} 句[/dim]')



if __name__ == "__main__":

    loc_data = 'datasets/ZuCo1.0'
    parser = argparse.ArgumentParser(description='Load EEG data from version 1 of the ZuCo dataset')
    parser.add_argument('--data_dir', type=str, default=loc_data, help='Path to the ZuCo data directory.')
    parser.add_argument('--save_data_dir', type=str, default=os.getcwd(), help='Path to save the processed dataset. Defaults to current working directory.')
    parser.add_argument('--labels_file', type=str, default=None, help="Path to the official sentiment_labels_task1.csv. Defaults to <data_dir 同级目录>/sentiment_labels_task1.csv.")

    args = parser.parse_args()

    ZuCo_data_v1(args.data_dir, args.save_data_dir, args.labels_file)





"""
dataset_dict = {
    subjectA: [sent_obj, ...],   # 来自 subjectA 的 .mat
    subjectB: [sent_obj, ...],   # 来自 subjectB 的 .mat
    ...
}
"""

"""
dataset_dict (dict)
 └── <subject_name> (str, 由文件名解析) : list
      │
      └── sent_obj (dict)   ← 每个有效句子的结构
           │
           ├── "content" : str                          # 句子文本
           │
           ├── "sentiment_label" : float                # ◀ 仅 task1-SR 存在（-1/0/1 = 负/中/正，匹配不到为 None）
           │
           ├── "sentence_level_EEG" (dict)              # 整句 8 个频带均值
           │    ├── mean_t1  mean_t2   (theta)
           │    ├── mean_a1  mean_a2   (alpha)
           │    ├── mean_b1  mean_b2   (beta)
           │    └── mean_g1  mean_g2   (gamma)
           │
           ├── "answer_EEG" (dict)   ◀ 仅 task1-SR 存在
           │    ├── answer_mean_t1  answer_mean_t2
           │    ├── answer_mean_a1  answer_mean_a2
           │    ├── answer_mean_b1  answer_mean_b2
           │    └── answer_mean_g1  answer_mean_g2
           │
           ├── "word" : list                            # 有注视(fixation)的词
           │    │
           │    └── word_obj (dict)   ← 仅 nFixations>0 的词
           │         ├── "content" : str
           │         ├── "n_fixations" : int
           │         └── "word_level_EEG" (dict)        # 每个词 3 类 × 8 频带
           │              ├── "FFD"   : {FFD_t1, FFD_t2, FFD_a1, FFD_a2,
           │              │             FFD_b1, FFD_b2, FFD_g1, FFD_g2}
           │              ├── "TRT"   : {TRT_* 同上 8 个}
           │              └── "GD"    : {GD_*  同上 8 个}
           │
           ├── "word_tokens_has_fixation" : list[str]   # 有注视词内容
           ├── "word_tokens_with_mask" : list[str]      # 无注视词用 "[MASK]" 占位
           └── "word_tokens_all" : list[str]            # 该句全部词内容
"""
