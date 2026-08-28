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


def ZuCo_data_v1(data_dir, save_data_dir):

    console = Console()

    EEG_data = os.path.join(save_data_dir, 'EEG_data')
    os.makedirs(EEG_data, exist_ok=True)

    # Loop over the three tasks
    tasks = ['task1-SR', 'task2-NR', 'task3-TSR']

    for task in tasks:
        # 主任务不用进度条，直接打印任务名称（打印时没有活动的进度条重绘，避免错位）
        console.print(f'\n[bold cyan]{task}[/bold cyan]')

        input_mat_files_dir = os.path.join(data_dir, task, 'Matlab_files')
        mat_files = os.listdir(input_mat_files_dir)
        path_mat_files = [os.path.join(input_mat_files_dir, mat_file) for mat_file in mat_files]
        dataset_dict = {} # 存储每个主体的句子数据
        
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
                for sent in mat_data:

                    word_data = sent.word
                    # 如果这句是有效的句子，才处理
                    if not isinstance(word_data, float):

                        # First key: sentence content
                        sent_obj = {'content': sent.content}

                        # second key: Oscillatory in different power bands (Theta, Alpha, Beta, Gamma)
                        sent_obj['sentence_level_EEG'] = {'mean_t1': sent.mean_t1, 'mean_t2': sent.mean_t2,
                                                        'mean_a1': sent.mean_a1, 'mean_a2': sent.mean_a2,
                                                        'mean_b1': sent.mean_b1, 'mean_b2': sent.mean_b2,
                                                        'mean_g1': sent.mean_g1, 'mean_g2': sent.mean_g2}

                        if task == 'task1-SR':
                            # task1-SR: Read sentences, answer control questions
                            sent_obj['answer_EEG'] = {'answer_mean_t1': sent.answer_mean_t1,
                                                    'answer_mean_t2': sent.answer_mean_t2,
                                                    'answer_mean_a1': sent.answer_mean_a1,
                                                    'answer_mean_a2': sent.answer_mean_a2,
                                                    'answer_mean_b1': sent.answer_mean_b1,
                                                    'answer_mean_b2': sent.answer_mean_b2,
                                                    'answer_mean_g1': sent.answer_mean_g1,
                                                    'answer_mean_g2': sent.answer_mean_g2}

                        # world level data
                        sent_obj['word'] = []

                        # Features from eye-tracking
                        word_tokens_has_fixation = []
                        word_tokens_all = []
                        word_tokens_with_mask = []

                        for word in word_data:
                            word_obj = {'content': word.content}
                            word_obj['n_fixations'] = word.nFixations

                            # 如果这个词有fixation，才处理
                            if isinstance(word.nFixations, (int, np.integer)) and word.nFixations > 0:

                                word_obj['word_level_EEG'] = {'FFD': {'FFD_t1': word.FFD_t1, 'FFD_t2': word.FFD_t2,
                                                                    'FFD_a1': word.FFD_a1, 'FFD_a2': word.FFD_a2,
                                                                    'FFD_b1': word.FFD_b1, 'FFD_b2': word.FFD_b2,
                                                                    'FFD_g1': word.FFD_g1, 'FFD_g2': word.FFD_g2}}

                                word_obj['word_level_EEG']['TRT'] = {'TRT_t1': word.TRT_t1, 'TRT_t2': word.TRT_t2,
                                                                    'TRT_a1': word.TRT_a1, 'TRT_a2': word.TRT_a2,
                                                                    'TRT_b1': word.TRT_b1, 'TRT_b2': word.TRT_b2,
                                                                    'TRT_g1': word.TRT_g1, 'TRT_g2': word.TRT_g2}
                                word_obj['word_level_EEG']['GD'] = {'GD_t1': word.GD_t1, 'GD_t2': word.GD_t2,
                                                                    'GD_a1': word.GD_a1, 'GD_a2': word.GD_a2,
                                                                    'GD_b1': word.GD_b1, 'GD_b2': word.GD_b2,
                                                                    'GD_g1': word.GD_g1, 'GD_g2': word.GD_g2}
                                
                                sent_obj['word'].append(word_obj)
                                word_tokens_all.append(word.content)
                                word_tokens_has_fixation.append(word.content)
                                word_tokens_with_mask.append(word.content)

                            else:
                                # 如果这个词没有fixation，用MASK代替
                                word_tokens_with_mask.append('[MASK]')
                                continue

                        sent_obj['word_tokens_has_fixation'] = word_tokens_has_fixation
                        sent_obj['word_tokens_with_mask'] = word_tokens_with_mask
                        sent_obj['word_tokens_all'] = word_tokens_all

                        dataset_dict[subject_name].append(sent_obj)

                    time.sleep(0.001)
                    progress.advance(task_id, advance = 1)

     

        # save the dataset_dict for each task
        output_file = f'{task}_v1.pkl'
        with open(os.path.join(EEG_data, output_file), 'wb') as handle:
            pickle.dump(dataset_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)



if __name__ == "__main__":

    loc_data = 'datasets/ZuCo1.0'
    parser = argparse.ArgumentParser(description='Load EEG data from version 1 of the ZuCo dataset')
    parser.add_argument('--data_dir', type=str, default=loc_data, help='Path to the ZuCo data directory.')
    parser.add_argument('--save_data_dir', type=str, default=os.getcwd(), help='Path to save the processed dataset. Defaults to current working directory.')

    args = parser.parse_args()

    ZuCo_data_v1(args.data_dir, args.save_data_dir)