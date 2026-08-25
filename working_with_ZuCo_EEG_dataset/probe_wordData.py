"""探查 ZuCo mat 文件中 wordData 的所有字段名与形状。

用法:
    python probe_wordData.py <path/to/xxx.mat>
不带参数时使用默认的 task1-SR 文件。
"""
import sys
import numpy as np
import scipy.io as io


def describe(obj, path='wordData', depth=0, max_depth=6):
    """递归打印 matlab 对象的字段名和数组形状。"""
    indent = '    ' * depth

    # mat_struct 类型 (struct_as_record=False 时载入)
    if hasattr(obj, '_fieldnames'):
        for name in obj._fieldnames:
            describe(getattr(obj, name), f'{path}.{name}', depth + 1, max_depth)

    # numpy void 结构体 (dtype 带字段名)
    elif isinstance(obj, np.void):
        for name in obj.dtype.names:
            describe(obj[name], f'{path}.{name}', depth + 1, max_depth)

    # 数组
    elif isinstance(obj, np.ndarray):
        if obj.dtype.names:  # 结构体数组
            print(f'{indent}{path}: <struct array> shape={obj.shape}')
            flat = obj.ravel()
            if flat.size and depth + 1 <= max_depth:
                describe(flat[0], f'{path}[0]', depth + 1, max_depth)
        elif obj.ndim == 0:
            val = obj.item()
            if isinstance(val, str):
                print(f'{indent}{path}: string = {val!r}')
            else:
                print(f'{indent}{path}: scalar dtype={obj.dtype} value={val}')
        elif obj.dtype == object:  # object 数组，逐元素递归 (rawEEG/rawET)
            print(f'{indent}{path}: <object array> shape={obj.shape}')
            if depth + 1 <= max_depth:
                for idx, item in enumerate(obj.ravel()):
                    describe(item, f'{path}[{idx}]', depth + 1, max_depth)
        else:
            # MATLAB 字符串数组 (字符数组)
            if obj.dtype.kind == 'U' or obj.dtype.char in ('c', 'S'):
                print(f'{indent}{path}: <char array> shape={obj.shape} repr={np.array2string(obj.ravel()[:20])}')
            else:
                n_show = 8  # 只展示前几个数值，避免大矩阵刷屏
                flat = obj.ravel()[:n_show]
                print(f'{indent}{path}: array shape={obj.shape} dtype={obj.dtype} '
                      f'first={np.array2string(flat, precision=4)}')

    # Python 原生类型
    elif isinstance(obj, (str, int, float)):
        print(f'{indent}{path}: {type(obj).__name__} = {obj!r}')
    else:
        print(f'{indent}{path}: <{type(obj).__name__}>')


def main(mat_file):
    print(f'== 读取: {mat_file}')
    mat_data = io.loadmat(mat_file, squeeze_me=True, struct_as_record=False)['sentenceData']

    for i, sent in enumerate(mat_data):
        word_data = sent.word
        if isinstance(word_data, float):   # 空句子 (无数词)，跳过
            continue
        print(f'\n== 第一个有效句子 [idx={i}] content={sent.content!r}')
        # 整句原始 EEG 信号
        print(f'\n-- 整句原始 EEG (sentence.rawData):')
        describe(sent.rawData, 'sentence.rawData')
        print(f'\n-- wordData:')
        print(f'wordData 类型: {type(word_data).__name__}')
        # squeeze 后单词是 struct，多词是 struct 数组；统一按数组处理
        words = np.atleast_1d(word_data)
        first_word = words.ravel()[0]
        print(f'\n== 第一个词的字段名及形状:')
        describe(first_word, 'word[0]')
        print(f'\n== 词的数量: {len(words.ravel())}')
        break


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else \
        'datasets/ZuCo1.0/task1-SR/Matlab_files/resultsZDN_SR.mat'
    main(path)

# import scipy.io as io
# import numpy as np

# p = 'datasets/ZuCo1.0/task1-SR/Matlab_files/resultsZDN_SR.mat'
# md = io.loadmat(p, squeeze_me=True, struct_as_record=False)
# s0 = md['sentenceData'][0]
# rd = s0.rawData                          # 整句原始信号 (105, 4212)
# e0 = np.atleast_1d(s0.word)[0].rawEEG[0] # 该词第一次注视 (105, 108)

# seg = rd[:, 321:321 + 108]               # 整句里截取对应片段
# print(np.array_equal(seg, e0))           # True → 完全相等
# print(np.abs(seg - e0).max())            # 0.0