"""用 mat73 重写 ZuCo 2.0 数据加载脚本，对应原 load_data_v2.py。

与原 h5py 版的区别：
- 原版 `h5py.File` + 手动 `[idx][0]` 解引用 + `load_matlab_string` 解码字符串
- 本版一次性用 `mat73.loadmat()` 读入，mat73 已自动完成：
    struct -> dict, struct数组 -> list[dict], cell -> list,
    char -> str（自动解码）, 数值 -> ndarray（自动 squeeze）,
    HDF5 对象引用 -> 自动解引用
因此不再依赖 utils_load_data_v2.py 里的 h5py 辅助函数。
"""

import os
import numpy as np
import mat73
from tqdm import tqdm
import pickle
import argparse


def as_list(x):
    """把 mat73 还原出的『一个词/一个句子』统一成列表，方便逐个遍历。"""
    if x is None:
        return []
    if isinstance(x, dict):
        return [x]
    if isinstance(x, (list, tuple)):
        return list(x)
    if isinstance(x, np.ndarray):
        return list(x.ravel())
    return [x]


def to_scalar(x):
    """把 mat73 还原出的标量统一成 Python 标量（可能是 ndarray/0-d）。"""
    if isinstance(x, np.ndarray):
        flat = x.ravel()
        return flat[0] if flat.size else None
    return x


def get_band(word, prefix):
    """从一个词的频带特征里取某眼动指标对应的 8 个频带。"""
    return {f'{prefix}_t1': word[f'{prefix}_t1'],
            f'{prefix}_t2': word[f'{prefix}_t2'],
            f'{prefix}_a1': word[f'{prefix}_a1'],
            f'{prefix}_a2': word[f'{prefix}_a2'],
            f'{prefix}_b1': word[f'{prefix}_b1'],
            f'{prefix}_b2': word[f'{prefix}_b2'],
            f'{prefix}_g1': word[f'{prefix}_g1'],
            f'{prefix}_g2': word[f'{prefix}_g2']}


def ZuCo_data_v2_mat73(data_dir, save_data_dir, verbose=True):

    EEG_data = os.path.join(save_data_dir, 'EEG_data')
    os.makedirs(EEG_data, exist_ok=True)

    task = 'NR'
    root_directory = os.path.join(data_dir, f'task2-{task}-2.0/Matlab_files')

    if verbose:
        print('Loading data from ZuCo v2.0 from ', root_directory)
        print('__________________________________________')
        print('Saving processed data to ', EEG_data)

    dataset_dict = {}

    for file in tqdm(os.listdir(root_directory), desc='MAT files'):
        if file.endswith(f'{task}.mat'):
            file_name = os.path.join(root_directory, file)

            # 从文件名提取被试 id，例如 resultsZAB_NR.mat -> ZAB
            subject = os.path.basename(file_name).split('results')[1].split('_')[0]
            if verbose:
                print('Processing subject ', subject)

            # 排除 YMH：数据不完整（阅读障碍被试）
            if subject == 'YMH':
                continue

            assert subject not in dataset_dict
            dataset_dict[subject] = []

            # mat73 一次性读入整个文件，返回嵌套 dict
            data = mat73.loadmat(file_name)
            sentences = data['sentenceData']  # 每句一个 dict 的列表

            # sentenceData 是 1×N struct 数组；mat73 可能退化成单 dict，统一成列表
            sentences = as_list(sentences)

            for sent_raw in sentences:
                sent_string = sent_raw['content']
                sent_obj = {'content': sent_string}

                # 句子级频带特征 (mat73 已 squeeze，这里再保一遍)
                sent_obj['sentence_level_EEG'] = {
                    'mean_t1': np.squeeze(sent_raw['mean_t1']),
                    'mean_t2': np.squeeze(sent_raw['mean_t2']),
                    'mean_a1': np.squeeze(sent_raw['mean_a1']),
                    'mean_a2': np.squeeze(sent_raw['mean_a2']),
                    'mean_b1': np.squeeze(sent_raw['mean_b1']),
                    'mean_b2': np.squeeze(sent_raw['mean_b2']),
                    'mean_g1': np.squeeze(sent_raw['mean_g1']),
                    'mean_g2': np.squeeze(sent_raw['mean_g2']),
                }

                sent_obj['word'] = []
                word_tokens_all = []
                word_tokens_has_fixation = []
                word_tokens_with_mask = []

                # 每个词还原成一个 dict，字段与 MATLAB 结构同名
                for word in as_list(sent_raw['word']):
                    word_content = word['content']
                    word_tokens_all.append(word_content)
                    word_obj = {'content': word_content}

                    n_fix = to_scalar(word.get('nFixations'))
                    word_obj['nFixations'] = n_fix

                    # 有注视的词才有词级 EEG 频带特征
                    if isinstance(n_fix, (int, np.integer)) and n_fix > 0:
                        word_obj['word_level_EEG'] = {
                            'GD':  get_band(word, 'GD'),
                            'FFD': get_band(word, 'FFD'),
                            'TRT': get_band(word, 'TRT'),
                        }
                        sent_obj['word'].append(word_obj)
                        word_tokens_has_fixation.append(word_content)
                        word_tokens_with_mask.append(word_content)
                    else:
                        word_tokens_with_mask.append('[MASK]')

                if len(word_tokens_all) == 0:
                    if verbose:
                        print(f'no word level features: subj:{subject} content:{sent_string}, append None')
                    dataset_dict[subject].append(None)
                    continue

                sent_obj['word_tokens_has_fixation'] = word_tokens_has_fixation
                sent_obj['word_tokens_with_mask'] = word_tokens_with_mask
                sent_obj['word_tokens_all'] = word_tokens_all

                dataset_dict[subject].append(sent_obj)

    task_name = 'task2-NR-2.0'

    if dataset_dict == {}:
        print(f'No mat file found for {task_name}')
        quit()

    output_name = f'{task_name}-dataset.pickle'
    with open(os.path.join(EEG_data, output_name), 'wb') as handle:
        pickle.dump(dataset_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
        print('write to:', os.path.join(EEG_data, output_name))


if __name__ == '__main__':
    loc_data = 'datasets/ZuCo2.0'  # 自行改成你的 ZuCo 2.0 数据根目录
    parser = argparse.ArgumentParser(description='Load EEG data from version 2 of the ZuCo dataset (mat73)')
    parser.add_argument('--data_dir', type=str, default=loc_data,
                        help='Path to the ZuCo v2.0 data directory.')
    parser.add_argument('--save_data_dir', type=str, default=os.getcwd(),
                        help='Path to save the processed dataset. Defaults to current working directory.')
    parser.add_argument('--verbose', action='store_true', help='Increase output verbosity.')

    args = parser.parse_args()

    ZuCo_data_v2_mat73(args.data_dir, args.save_data_dir, args.verbose)