import pickle
import os
import argparse


def analyze_pkl_v2(data_dir):
    """读取 load_data_v2_mat73.py 生成的 ZuCo2.0 pkl，统计每个 pkl 的 subject_name 数量及每个 subject_name 的句子数。"""
    tasks = ['task1-NR', 'task2-TSR']

    for task in tasks:
        pkl_path = os.path.join(data_dir, f'{task}-v2.pkl')
        if not os.path.exists(pkl_path):
            print(f'[SKIP] 文件不存在: {pkl_path}')
            continue

        with open(pkl_path, 'rb') as f:
            dataset_dict = pickle.load(f)

        print(f'\n=== {task} ({os.path.basename(pkl_path)}) ===')
        print(f'subject 数量: {len(dataset_dict)}')

        total_sents = 0
        for subject_name, sent_list in dataset_dict.items():
            num_sents = len(sent_list)
            total_sents += num_sents
            print(f'  {subject_name}: {num_sents} 句')
            # parsed_sents = [parse_sentences(sent_obj) for sent_obj in sent_list]
            # for sent in parsed_sents:
            #     print(sent)

        print(f'句子总数: {total_sents}')


def parse_sentences(sent_obj):
    """从单个 sent_obj 中统计单词信息，可用于核对数据结构。"""
    return {
        'content': sent_obj.get('content'),
        'num_words': len(sent_obj.get('word_tokens_all', [])),
        'num_words_has_fixation': len(sent_obj.get('word_tokens_has_fixation', [])),
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='统计 ZuCo2.0 pkl 中每个 subject 的句子数量')
    parser.add_argument('--data_dir', type=str, default='EEG_data/ZuCo2.0', help='ZuCo2.0 pkl 目录')
    args = parser.parse_args()

    analyze_pkl_v2(args.data_dir)