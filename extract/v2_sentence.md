## h5py format
```text
allFixations Dataset (349, 1)
content Dataset (349, 1)
mean_a1 Dataset (349, 1)
mean_a1_diff Dataset (349, 1)
mean_a2 Dataset (349, 1)
mean_a2_diff Dataset (349, 1)
mean_b1 Dataset (349, 1)
mean_b1_diff Dataset (349, 1)
mean_b2 Dataset (349, 1)
mean_b2_diff Dataset (349, 1)
mean_g1 Dataset (349, 1)
mean_g1_diff Dataset (349, 1)
mean_g2 Dataset (349, 1)
mean_g2_diff Dataset (349, 1)
mean_t1 Dataset (349, 1)
mean_t1_diff Dataset (349, 1)
mean_t2 Dataset (349, 1)
mean_t2_diff Dataset (349, 1)
omissionRate Dataset (349, 1)
rawData Dataset (349, 1)
word Dataset (349, 1)
wordbounds Dataset (349, 1)
```

```text
sentenceData (Group)
├── content    (ref array) ──指向──> Dataset  (句子文本)
├── rawData    (ref array) ──指向──> Dataset  (整句EEG矩阵)
└── word       (ref array) ──指向──> Group    (单词struct)
                                      ├── content    (词文本)
                                      ├── rawEEG     (该词的EEG切片)
                                      ├── rawET      (该词的眼动)
                                      └── fixPositions ...
```
## mat73 format
```text
allFixations list 349
content list 349
mean_a1 list 349
mean_a1_diff list 349
mean_a2 list 349
mean_a2_diff list 349
mean_b1 list 349
mean_b1_diff list 349
mean_b2 list 349
mean_b2_diff list 349
mean_g1 list 349
mean_g1_diff list 349
mean_g2 list 349
mean_g2_diff list 349
mean_t1 list 349
mean_t1_diff list 349
mean_t2 list 349
mean_t2_diff list 349
omissionRate list 349
rawData list 349
word list 349
wordbounds list 349
```