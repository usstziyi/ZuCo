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
import mat73
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
    # root
    mat_root = io.loadmat(mat_file, squeeze_me=True, struct_as_record=False) # dict
    for name in mat_root.keys():
        print(name)
    

    # sentence
    sentences = io.loadmat(mat_file, squeeze_me=True, struct_as_record=False)['sentenceData'] # numpy.ndarray

    sentence = sentences[0] # mat_struct

    # for name in sentence._fieldnames:
    #     v = getattr(sentence, name)
    #     print(name, type(v).__name__, getattr(v, 'shape', ''))
    
    content = sentence.content # 当前句子内容,str
    print(content)

    rawData = sentence.rawData # 当前句子完整EEG信号,ndarray
    print(rawData.shape)

    # word
    word = sentence.word # 当前句子单词，ndarray
    print(word.shape)

    word_0 = word[0] # 当前句子第一个单词，mat_struct
    print(type(word_0))

    # for name in word_0._fieldnames:
    #     v = getattr(word_0, name)
    #     print(name, type(v).__name__, getattr(v, 'shape', ''))

    content = word_0.content # 当前句子第一个单词内容,str
    print(content)


    for rawEEG in word_0.rawEEG:
        print(rawEEG.shape)

    for rawET in word_0.rawET:
        print(rawET.shape)

    for fixPosition in word_0.fixPositions:
        print(fixPosition)
    

    return


def main_v2_h5py(mat_file):
    with h5py.File(mat_file, 'r') as f:
        sentences = f['sentenceData'] # h5py._hl.group.Group
        # for name in sentences.keys():
        #     print(name, type(sentences[name]).__name__, sentences[name].shape)

        content = sentences['content'] # h5py._hl.dataset.Dataset
        print(content.shape)

        col = content[0] # numpy.ndarray
        print(col.shape)

        ref = col[0] # 里面装着第 0 句的那个 HDF5 对象引用，指向第 0 句文本所在的那个 Dataset
        print(type(ref)) # h5py.h5r.Reference

        target = f[ref] # h5py._hl.dataset.Dataset
        print(type(target)) 
        print(target.shape)
        # print(target.name) # /#refs#/b

        # 第0句的真实文本
        text = ''.join(chr(int(c)) for c in target[:, 0])
        print(text)
        # 一步到位
        target = f[content[(0, 0)]]
        text = ''.join(chr(int(c)) for c in target[:, 0])
        print(text)

        rawData = sentences['rawData'] # h5py._hl.dataset.Dataset
        print(rawData.shape)

        target = f[rawData[(0, 0)]] # h5py._hl.dataset.Dataset
        print(target.shape) # 维度顺序和 ZuCo 1.0 相反
        print(target.dtype) # float64

        word = sentences['word'] # h5py._hl.dataset.Dataset
        print(word.shape)

        target = f[word[(0, 0)]] # h5py._hl.group.Group
        for name in target.keys():
            print(name, type(target[name]).__name__, target[name].shape)

        
def main_v2_mat73(mat_file):
    # mat root
    data = mat73.loadmat(
        file = mat_file,
        use_attrdict=False,
    ) # dict
    
    # 所有sentences
    sentences = data['sentenceData'] # mat73.core.AttrDict


    for name in sentences.keys():
        v = sentences[name]    
        length = len(v) if isinstance(v, list) else ''
        print(name, type(v).__name__, length)
    
    # content/sentence
    content = sentences['content'] # list
    # 第0个句子的内容，str
    sentence = content[0] # str
    print(sentence)

    # 所有word
    word = sentences['word'] # list

    # 第0个句子的全部单词
    w = word[0] # mat73.core.AttrDict

    for name in w.keys():
        v = w[name]
        length = len(v) if isinstance(v, list) else ''
        print(name, type(v).__name__, length)

    w_content = w['content'] # list
    # 第0个句子的第0个单词内容，str
    print(w_content[0])
    # 第0个句子的单词内容，str
    print(w_content)
    





    


def main(mat_file):
    print(f'== 读取: {mat_file}')
    if h5py.is_hdf5(mat_file):
        main_v2_mat73(mat_file)
    else:
        main_v1(mat_file)


if __name__ == '__main__':
    # path = 'datasets/ZuCo1.0/task1-SR/Matlab_files/resultsZDN_SR.mat'
    path = 'datasets/ZuCo2.0/task1-NR/Matlab_files/resultsYAC_NR.mat'
    main(path)