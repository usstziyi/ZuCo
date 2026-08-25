"""探查 ZuCo mat 文件中 wordData 的所有字段名与形状。

同时兼容 ZuCo 1.0 与 ZuCo 2.0：
  - ZuCo 1.0：旧版 mat (v7)，用 scipy.io.loadmat，字段直接挂在 mat_struct 上
  - ZuCo 2.0：mat 7.3 (HDF5)，用 h5py，字段值多为“对象引用数组”，
    需先取引用再 f[ref] 解引用；本脚本会自动识别格式。

用法:
    python probe_wordData.py <path/to/xxx.mat>
不带参数时使用默认的 task1-SR 文件。
"""
import sys
import numpy as np
import h5py
import scipy.io as io


def node_fields(node, file=None):
    """返回对象的 (字段名, 字段值) 列表；无法枚举(如标量/数组)时返回 None。"""
    # ZuCo 1.0：MATLAB struct (struct_as_record=False 时载入)
    if hasattr(node, '_fieldnames'):
        return [(name, getattr(node, name)) for name in node._fieldnames]
    # ZuCo 1.0：numpy void 结构体
    if isinstance(node, np.void) and node.dtype.names:
        return [(name, node[name]) for name in node.dtype.names]
    # ZuCo 2.0：h5py Group（一批字段组织在一起）
    if file is not None and isinstance(node, h5py.Group):
        return [(name, node[name]) for name in node.keys()]
    return None


def describe(node, path='wordData', depth=0, max_depth=8, file=None):
    """递归打印 mlab/h5py 对象的字段名和数组形状。"""
    indent = '    ' * depth
    if depth > max_depth:  # 防止过深导致刷屏
        print(f'{indent}{path}: ...(已达最大深度)')
        return

    # 1) 能枚举子字段的对象：struct / void / h5py Group，逐字段递归
    sub = node_fields(node, file)
    if sub is not None:
        for name, val in sub:
            describe(
                node = val, 
                path = f'{path}.{name}', 
                depth = depth + 1, 
                max_depth = max_depth, 
                file = file
            )
        return

    # 2) ZuCo 2.0：对象引用数组（HDF5 object reference），逐引用递归解引用
    if file is not None and isinstance(node, h5py.Dataset) and node.dtype.kind == 'O':
        refs = np.asarray(node[...]).ravel()
        print(f'{indent}{path}: <ref array> shape={node.shape} dtype=object ({len(refs)} refs)')
        # 只取下界第一个引用递归，探查脚本无需展开全部
        for i in range(min(1, len(refs))):
            describe(file[refs[i]], f'{path}[{i}]', depth + 1, max_depth, file)
        return

    # 3) ZuCo 2.0：Entity数值/字符串 dataset
    if file is not None and isinstance(node, h5py.Dataset):
        arr = node[...]
        # MATLAB 字符串在 h5py 中是 uint16 的 (n,1) 字符数组
        if arr.ndim == 2 and arr.shape[1] == 1 and arr.dtype.kind in 'iu' and arr.shape[0] > 0:
            s = ''.join(chr(int(x)) for x in arr.ravel())
            print(f'{indent}{path}: string = {s!r}')
        else:
            flat = np.asarray(arr).ravel()
            print(f'{indent}{path}: array shape={arr.shape} dtype={arr.dtype} '
                  f'first={np.array2string(flat[:8], precision=4)}')
        return

    # 4) ZuCo 1.0 的数组
    if isinstance(node, np.ndarray):
        if node.dtype.names:  # 结构体数组
            print(f'{indent}{path}: <struct array> shape={node.shape}')
            flat = node.ravel()
            if flat.size and depth + 1 <= max_depth:
                describe(flat[0], f'{path}[0]', depth + 1, max_depth, file)
        elif node.ndim == 0:
            val = node.item()
            if isinstance(val, (str, int, float)):
                print(f'{indent}{path}: scalar {type(val).__name__} = {val!r}')
            else:
                print(f'{indent}{path}: scalar dtype={node.dtype} value={val}')
        elif node.dtype == object:  # object 数组，逐元素递归 (rawEEG/rawET)
            print(f'{indent}{path}: <object array> shape={node.shape}')
            if depth + 1 <= max_depth:
                for idx, item in enumerate(node.ravel()):
                    describe(item, f'{path}[{idx}]', depth + 1, max_depth, file)
        else:
            # MATLAB 字符串数组 (字符数组)
            if node.dtype.kind == 'U' or node.dtype.char in ('c', 'S'):
                print(f'{indent}{path}: <char array> shape={node.shape} '
                      f'repr={np.array2string(node.ravel()[:20])}')
            else:
                n_show = 8  # 只展示前几个数值，避免大矩阵刷屏
                flat = node.ravel()[:n_show]
                print(f'{indent}{path}: array shape={node.shape} dtype={node.dtype} '
                      f'first={np.array2string(flat, precision=4)}')
        return

    # 5) Python 原生类型
    if isinstance(node, (str, int, float)):
        print(f'{indent}{path}: {type(node).__name__} = {node!r}')
    else:
        print(f'{indent}{path}: <{type(node).__name__}>')


def main_v1(mat_file):
    """ZuCo 1.0：scipy.io.loadmat 读取。"""
    mat_root = io.loadmat(mat_file, squeeze_me=True, struct_as_record=False) # dict
    print(mat_root.keys())
    
    sentences = io.loadmat(mat_file, squeeze_me=True, struct_as_record=False)['sentenceData'] # numpy.ndarray

    sentence = sentences[0] # mat_struct

    for name in sentence._fieldnames:
        v = getattr(sentence, name)
        print(name, type(v).__name__, getattr(v, 'shape', ''))
    
  
    for i, sentence in enumerate(sentences):
        word = sentence.word # 当前句子单词数量
        if isinstance(word, float):
            continue
        content = sentence.content # 当前句子内容
        print(content)

        rawData = sentence.rawData # 当前句子完整EEG信号,ndarray
        print(rawData.shape)

        print(rawData.dtype)
        return
   

        describe(
            node = sentence.rawData, 
            path = 'sentence.rawData'
        ) # 当前句子完整EEG信号

        return

        print(f'\n-- wordData:')
        print(f'wordData 类型: {type(word_data).__name__}')
        # squeeze 后单词是 struct，多词是 struct 数组；统一按数组处理
        words = np.atleast_1d(word_data)
        first_word = words.ravel()[0]
        print(f'\n== 第一个词的字段名及形状:')
        describe(first_word, 'word[0]')
        print(f'\n== 词的数量: {len(words.ravel())}')
        break


def main_v2(mat_file):
    """ZuCo 2.0：h5py 读取，字段为对象引用数组，统一交给 describe 解引用。"""
    with h5py.File(mat_file, 'r') as f:
        sd = f['sentenceData']

        print('\n== sentenceData 顶层字段:')
        describe(sd, 'sentenceData', file=f)

        print('\n-- 整句原始 EEG (sentenceData.rawData，引用数组，第一句):')
        describe(sd['rawData'], 'sentenceData.rawData', file=f)

        print('\n-- 句子内容 (sentenceData.content，引用数组，第一句):')
        describe(sd['content'], 'sentenceData.content', file=f)

        print('\n-- wordData (sentenceData.word，引用数组，第一句的第一个词):')
        describe(sd['word'], 'sentenceData.word', file=f)


def main(mat_file):
    print(f'== 读取: {mat_file}')
    if h5py.is_hdf5(mat_file):
        main_v2(mat_file)
    else:
        main_v1(mat_file)


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else \
        'datasets/ZuCo1.0/task1-SR/Matlab_files/resultsZDN_SR.mat'
    main(path)