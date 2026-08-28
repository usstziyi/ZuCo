import os
import mat73
import scipy.io as io
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

def ZuCo_data_v2_mat73(data_dir, save_data_dir):

    console = Console()

    EEG_data = os.path.join(save_data_dir, 'EEG_data', 'ZuCo2.0')
    os.makedirs(EEG_data, exist_ok=True)

    tasks = ['task1-NR', 'task2-TSR']

    for task in tasks:

        console.print(f'\n[bold cyan]{task}[/bold cyan]')

        input_mat_files_dir = os.path.join(data_dir, task, 'Matlab_files')
        mat_files = os.listdir(input_mat_files_dir)
        path_mat_files = [os.path.join(input_mat_files_dir, mat_file) for mat_file in mat_files]
        dataset_dict = {} # 存储每个主体的句子数据

        for mat_file in path_mat_files:
            # get subject id from the file name
            subject_name = os.path.basename(mat_file).split('.')[0].replace('results', '').strip()
            # 排除 YMH：数据不完整（阅读障碍被试）
            if subject_name == 'YMH':
                continue
            dataset_dict[subject_name] = []

            # 一次性加载整个 mat 文件
            mat_data = mat73.loadmat(mat_file, use_attrdict=False) # dict
            sentences_data = mat_data['sentenceData'] # dict
            
            # 所有句子数据
            contents = sentences_data['content']  # list
            
            # 所有单词数据
            words_data = sentences_data['word']   # list
    
            # 所有句子EEG平均数据
            mean_fields = {field: sentences_data[field] for field in 
                          ['mean_t1', 'mean_t2', 'mean_a1', 'mean_a2', 
                           'mean_b1', 'mean_b2', 'mean_g1', 'mean_g2']}

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                MofNCompleteColumn(),
                TimeRemainingColumn(),
                TimeElapsedColumn(),
            ) as progress:

                task_id = progress.add_task("[red]" + subject_name, total=len(contents))

                # 取句子
                for sent_idx, sent_content in enumerate(contents):
                    # 获取当前句子的单词数据
                    word_data = words_data[sent_idx] # dict/array(nan)
            
                    # 判断当前句子的单词是否有效（mat73 解析为 dict，无效句子为 array(nan)）
                    if isinstance(word_data, dict):
                        # 句子内容
                        sent_obj = {'content': sent_content}
                    
                        # 句子级别的EEG平均特征
                        sent_obj['sentence_level_EEG'] = {
                            field: mean_fields[field][sent_idx] 
                            for field in mean_fields.keys()
                        }
                        # 提取单词级别的数据
                        word_contents = word_data['content']  # list of str
                        n_fixations = word_data['nFixations']  # list of int
                        
                        sent_obj['word'] = []
                        word_tokens_all = []
                        word_tokens_has_fixation = []
                        word_tokens_with_mask = []
                    
                        # 取当前句子的单词
                        for word_idx, word_content in enumerate(word_contents):
                            # 当前单词的 fixations 数量
                            n_fix = n_fixations[word_idx] # ndarray
                            
                            # 处理 nFixations 可能的类型
                            if np.size(n_fix) > 0:
                                n_fix = np.ravel(n_fix)[0]  # 展平后取第一个元素
                            else:
                                n_fix = 0                    # 空容器返回0
                            
                            # 无论是否有注视，都计入全部词 token
                            word_tokens_all.append(word_content)
                            
                            # 如果当前单词注视次数大于0
                            if isinstance(n_fix, (int, np.integer, float)) and n_fix > 0:
                                word_obj = {
                                    'content': word_content,
                                    'nFixations': int(n_fix)
                                }
                                
                                # 提取该词的 EEG 平均特征
                                word_obj['word_level_EEG'] = {
                                    'GD': get_band_from_lists(word_data, word_idx, 'GD'),
                                    'FFD': get_band_from_lists(word_data, word_idx, 'FFD'),
                                    'TRT': get_band_from_lists(word_data, word_idx, 'TRT'),
                                }
                                
                                sent_obj['word'].append(word_obj)
                                word_tokens_has_fixation.append(word_content)
                                word_tokens_with_mask.append(word_content)
                            else:
                                word_tokens_with_mask.append('[MASK]')
                    
                        sent_obj['word_tokens_has_fixation'] = word_tokens_has_fixation
                        sent_obj['word_tokens_with_mask'] = word_tokens_with_mask
                        sent_obj['word_tokens_all'] = word_tokens_all
                        
                        dataset_dict[subject_name].append(sent_obj)

                    time.sleep(0.001)
                    progress.advance(task_id, advance=1)
        
        output_file = f'{task}-v2.pkl'
        with open(os.path.join(EEG_data, output_file), 'wb') as handle:
            pickle.dump(dataset_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)


def get_band_from_lists(word_data, word_idx, prefix):
    """从 word_data 的列表中提取指定词的频带特征"""
    return {
        f'{prefix}_t1': word_data[f'{prefix}_t1'][word_idx],
        f'{prefix}_t2': word_data[f'{prefix}_t2'][word_idx],
        f'{prefix}_a1': word_data[f'{prefix}_a1'][word_idx],
        f'{prefix}_a2': word_data[f'{prefix}_a2'][word_idx],
        f'{prefix}_b1': word_data[f'{prefix}_b1'][word_idx],
        f'{prefix}_b2': word_data[f'{prefix}_b2'][word_idx],
        f'{prefix}_g1': word_data[f'{prefix}_g1'][word_idx],
        f'{prefix}_g2': word_data[f'{prefix}_g2'][word_idx],
    }


if __name__ == '__main__':
    loc_data = 'datasets/ZuCo2.0'  # 自行改成你的 ZuCo 2.0 数据根目录
    parser = argparse.ArgumentParser(description='Load EEG data from version 2 of the ZuCo dataset (mat73)')
    parser.add_argument('--data_dir', type=str, default=loc_data,
                        help='Path to the ZuCo v2.0 data directory.')
    parser.add_argument('--save_data_dir', type=str, default=os.getcwd(),
                        help='Path to save the processed dataset. Defaults to current working directory.')


    args = parser.parse_args()

    ZuCo_data_v2_mat73(args.data_dir, args.save_data_dir)